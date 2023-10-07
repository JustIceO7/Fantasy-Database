from flask import Flask, render_template, session, redirect, url_for, request, g, make_response
from flask_session import Session
from form import MembersForm, RegistrationForm, LoginForm, ApplicationForm, AcceptApplicantForm, ModifyMemberDetailsForm, BaseStorageForm, BaseStorageMovement, ItemArchiveForm, AddToItemArchiveForm, AddNewBaseForm, AddMissionForm, AcceptMissionForm, MissionSearchingForm, ForgotPasswordForm, PermissionForm, AddItemsToBase, DeleteItemsFromBase, PfpForm
from database import get_db, close_db
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from datetime import datetime
from functions import getPowerLevel, wordFilter, baseRanking
import os

"""
User Details:   Oya, 123, Founder
                Stella, 123, Branch Head (rest of the branch heads have the password 123)
Main
This database is a representation of a military organisation with ranks "Founder" > "Branch Head" > "Core Member" > "Inner Member" > "Outer Member"
where "Founder" is the highest rank and has all the priviledges after which comes the "Branch Heads", they have the ability to remove
or edit members from their designated "residence" base

Profile
Each member has a "power_level" based on their level which contributions to the bases overall "base power", their current missions are also
displayed if they accepted any. 

Bases
Each "Branch Head" can add,remove or move items from their base to other bases, within bases there is an item index which holds information 
on all the items within the bases which can be editted by "Branch Head" figures, to add a new item into the bases you need to first add it
into the item index

Missions
there is a missions board in which each member can "accept" a mission which will show up in profile upon "accepting" the mission, and receive
rewards on completion namely "contribution points" which is controlled by "Founder" or "Branch Head" rank figures. Missions can have limitations
such as rank required and party limit. Missions can be removed or closed which means that members can not join or leave the mission 
anymore "Branch Head" figures can view previously completed missions and see its party members which consists of current or former members 
of the organisation (if they completed the mission and was then kicked)

Members
the organisations current members can be searched in the members page but only "Founder" and "Branch" head can edit member details

Rankings
In the rankings page you can see the power_level of different bases and ranks. bases, branch heads, core members, inner members and outer members

Registration
After registering the users application will show up on the applications page which "Founder" or "Branch Head" level figures can either 
accept or reject and assign them their future "residences" and "rank"

Kicking
If a member is kicked out they will be moved into a former members database while also removing any details of them in login or missions
that are not completed

Founder priviledges
The Founder can change permission access to pages in profile (change rank needed to access the pages)
"""

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["UPLOAD_FOLDER"] = "static/pfp"
Session(app)
app.teardown_appcontext(close_db)

@app.before_request
def logged_in_user():
    g.user = session.get("user_name", None)
    g.rank = session.get("user_rank")
    g.rank_value = session.get("user_rank_value")
    g.residence = session.get("user_residence")
    g.id = session.get("user_id")
    db = get_db()
    user_data = db.execute(""" SELECT * FROM members WHERE member_id=?;""",(g.id,)).fetchone()
    #in case a member gets their rank or residence changed when they are still logged in
    if g.user is not None:
        if g.rank != user_data["rank"] or g.residence != user_data["residence"]:
            rank_value = db.execute(""" SELECT * FROM ranks WHERE rank=?""", (user_data["rank"],)).fetchone()
            g.rank = user_data["rank"]
            g.rank_value = rank_value["rank_value"]
            g.residence = user_data["residence"]
    #get permission needed for each page
    permissions = db.execute(""" SELECT * FROM permissions WHERE permission_id = 1;""").fetchone()
    page_permission = db.execute(""" SELECT * FROM ranks WHERE rank = ?; """, (permissions["permission_rank"],)).fetchone()
    g.permission_level = page_permission["rank_value"]
    g.permission_rank = page_permission["rank"]

def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            return redirect(url_for("login", next=request.url))
        data = request.cookies.get("time")
        #if cookie expires log them out
        if data is None:
            return redirect(url_for("login", next=request.url))
        return view(*args,**kwargs)
    return wrapped_view 

@app.route("/")
@app.route("/home")
def home():
    db = get_db()
    db.execute(""" UPDATE user_site_tracker SET home = home + 1 WHERE member_id = ?""",(g.id,))
    db.commit()
    return render_template("home.html", title="Home Page")

@app.route("/profile", methods=["GET","POST"])
@login_required
def profile():
    db = get_db()
    form = PfpForm()
    db.execute(""" UPDATE user_site_tracker SET profile = profile + 1 WHERE member_id = ?""",(g.id,))
    db.commit()
    #user_details
    user_profile = db.execute(""" SELECT * FROM members WHERE name = ?;""", (g.user,)).fetchone()
    #user_missions if they have any
    user_missions = db.execute(""" SELECT * FROM mission_management JOIN missions ON mission_management.mission_id = missions.mission_id WHERE member_id = ? AND (missions.mission_status = "Incomplete" OR missions.mission_status = "Closed");""", (g.id,)).fetchall()

    user_picture = db.execute(""" SELECT * FROM pfp WHERE member_id = ?;""", (g.id,)).fetchone()
    picture = user_picture["picture"]
    #picture upload from https://www.youtube.com/watch?v=I9BBGulrOmo
    if form.validate_on_submit():
        file = form.file.data
        
        #renaming each picture to make them unique to each member
        file.filename = file.filename.split(".")[0] + "_" + str(g.id) + "." + file.filename.split(".")[1]

        filename = secure_filename(file.filename)
        
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        #remove their old picture from pfp folder if it is not the default one and not their current one
        if picture != "default.jfif" and picture != filename:
            os.remove(os.path.join(app.config["UPLOAD_FOLDER"], picture))

        db.execute(""" UPDATE pfp SET picture = ? WHERE member_id = ?""", (file.filename,g.id))
        db.commit()

        user_picture = db.execute(""" SELECT * FROM pfp WHERE member_id = ?;""", (g.id,)).fetchone()
        picture = user_picture["picture"]

    return render_template("profile.html", title="Profile Page", user_profile=user_profile, user_missions=user_missions, form=form, picture=picture)

@app.route("/bases", methods=["GET","POST"])
@login_required
def bases():
    form = BaseStorageForm()
    db = get_db()

    if g.rank_value < g.permission_level:
        page = "Bases"
        return render_template("access_denier.html", required_rank=g.permission_rank ,page=page, title="Access Denied")

    db = get_db()
    db.execute(""" UPDATE user_site_tracker SET bases = bases + 1 WHERE member_id = ?""",(g.id,))
    db.commit()

    bases = db.execute(""" SELECT * FROM bases ORDER BY base_name;""").fetchall()
    storage = None
    base_power_levels = {}

    #calculating the overall power of the base based on its members
    for base in bases:
        power_recorder = 0
        people = db.execute(""" SELECT * FROM members WHERE residence = ?;""", (base["base_name"],)).fetchall()
        if people is None:
            base_power_levels.append(0)
        else:
            for person in people:
                power_recorder += int(person["power_level"])
        base_power_levels[base["base_name"]] = power_recorder
    
    #choices for filtering out items
    itemsList = db.execute(""" SELECT * FROM items ORDER BY item_name;""").fetchall()
    for item in itemsList:
        form.item.choices.append(item["item_name"])
    form.item.choices.append("Any")

    baseList = db.execute(""" SELECT * FROM bases ORDER BY base_name;""").fetchall()
    for base in baseList:
        form.base.choices.append(base["base_name"])
    form.base.choices.append("Any")

    rarityList = db.execute(""" SELECT * FROM rarity ORDER BY rarity;""").fetchall()
    for rarity in rarityList:
        form.rarity.choices.append(rarity["rarity"])
    form.rarity.choices.append("Any")

    if form.validate_on_submit():
        base = form.base.data
        item = form.item.data
        rarity = form.rarity.data
        if base == "Any":
            base = "%"
        if item == "Any":
            item = "%"
        if rarity == "Any":
            rarity = "%"
        storage = db.execute(""" SELECT * FROM storage WHERE base_name LIKE ? AND item_name LIKE ? AND item_rarity LIKE ? ORDER BY base_name;""", (base,item,rarity)).fetchall()
        if len(storage) == 0:
            storage = 0
    return render_template("bases.html", title="Bases Page",bases=bases, storage=storage, form=form, base_power_levels=base_power_levels)

@app.route("/base/<base_name>", methods=["GET","POST"])
@login_required
def base_details(base_name):
    db = get_db()

    if g.rank_value < g.permission_level:
        page = "Page"
        return render_template("access_denier.html", required_rank=g.permission_rank ,page=page, title="Access Denied")
    
    addform = AddItemsToBase()
    deleteform = DeleteItemsFromBase()
    moveform = BaseStorageMovement()

    itemsList = db.execute(""" SELECT * FROM items ORDER BY item_name;""").fetchall()
    for item in itemsList:
        addform.item_name1.choices.append(item["item_name"])

    if addform.validate_on_submit():
        item_name = addform.item_name1.data
        quantity = int(addform.quantity1.data)
        if quantity < 1:
            addform.quantity1.errors.append("Use Positive Numbers")
        else:
            item_rarity = db.execute(""" SELECT * FROM items WHERE item_name =?;""", (item_name,)).fetchone()

            item_checker = db.execute(""" SELECT * FROM storage WHERE item_name = ? AND base_name = ?;""", (item_name,base_name)).fetchone()

            #if item does not exist in storage add it otherwise just increment the values
            if item_checker == None:
                db.execute(""" INSERT INTO storage (base_name,item_name,item_rarity,quantity) VALUES (?,?,?,?);""", (base_name,item_name,item_rarity["rarity"],quantity))
                db.commit()
                return redirect(url_for('base_details', base_name=base_name))
            else:
                item_quantity = db.execute(""" SELECT * FROM storage WHERE base_name = ? AND item_name = ?;""", (base_name,item_name)).fetchone()
                newQuantity = quantity + int(item_quantity["quantity"])
                db.execute(""" UPDATE storage SET quantity = ? WHERE base_name = ? AND item_name = ?;""", (newQuantity,base_name,item_name))
                db.commit()
                return redirect(url_for('base_details', base_name=base_name))

    #see what items the base has to remove
    itemsList2 = db.execute(""" SELECT * FROM items;""").fetchall()
    sortedItems = []
    item_checker = db.execute(""" SELECT * FROM storage WHERE base_name = ?;""", (base_name,)).fetchall()
    
    allItems = []
    baseItems = []

    for item in itemsList2:
        allItems.append(item["item_name"])

    for item in item_checker:
        baseItems.append(item["item_name"])

    for item in allItems:
        if item in baseItems:
            sortedItems.append(item)

    sortedItems.sort()
    for item in sortedItems:
        deleteform.item_name2.choices.append(item)
        moveform.item_name3.choices.append(item)

    baseList = db.execute(""" SELECT * FROM bases ORDER BY base_name;""").fetchall()
    for base in baseList:
        moveform.moveTo.choices.append(base["base_name"])
    moveform.moveTo.choices.remove(base_name)

    if deleteform.validate_on_submit():
        item_name = deleteform.item_name2.data
        quantity = int(deleteform.quantity2.data)


        item_quantity_in_base = db.execute(""" SELECT * FROM storage WHERE base_name = ? AND item_name = ?;""", (base_name,item_name)).fetchone()

        quantity_in_base = int(item_quantity_in_base["quantity"])
       

        #trying to remove more than you have
        if quantity > quantity_in_base:
            deleteform.quantity2.errors.append("You dont have that much in the base")

        elif quantity < 0:
            deleteform.quantity2.errors.append("Use Positive Numbers")  

        #if removing item makes the quantity to 0 then remove it from database
        else:
            if quantity - quantity_in_base == 0:
                db.execute(""" DELETE FROM storage WHERE base_name = ? AND item_name = ?;""", (base_name,item_name))
                db.commit()
                return redirect(url_for('base_details', base_name=base_name))
            else:
                newQuantity = quantity_in_base - quantity
                db.execute(""" UPDATE storage SET quantity = ? WHERE base_name = ? AND item_name = ?;""", (newQuantity,base_name,item_name))
                db.commit()
                return redirect(url_for('base_details', base_name=base_name))

    if moveform.validate_on_submit():
        item_name = moveform.item_name3.data
        newBase = moveform.moveTo.data
        quantity = int(moveform.quantity.data)

        item_details = db.execute(""" SELECT * FROM items WHERE item_name =?""",(item_name,)).fetchone()

        max_amount = db.execute(""" SELECT * FROM storage WHERE item_name =? AND base_name =?""", (item_name,base_name)).fetchone()

        #try to move more than you have
        if quantity > int(max_amount["quantity"]):
            moveform.quantity.errors.append("Error Max Amount Surpassed")
        elif quantity < 0:
            moveform.quantity.errors.append("Use Positive Numbers")
        else:
            newQuantity = int(max_amount["quantity"]) - quantity

            #if storage is 0 of the item then adds to database else just increment values
            emptyCheck = db.execute(""" SELECT * FROM storage WHERE base_name = ? AND item_name = ?;""", (newBase,item_name)).fetchone()
            if emptyCheck is None:
                db.execute(""" INSERT INTO storage (base_name,item_name,item_rarity,quantity) VALUES (?,?,?,?)""", (newBase,item_name,item_details["rarity"],0))
                db.commit()
            
            if newQuantity == 0:
                db.execute(""" DELETE FROM storage WHERE base_name = ? AND item_name = ?;""", (base_name,item_name))
                db.commit()
            else:
                db.execute(""" UPDATE storage SET quantity = ? WHERE base_name = ? AND item_name = ?; """, (newQuantity,base_name,item_name))
                db.commit()
            
            db.execute(""" UPDATE storage SET quantity = quantity + ? WHERE base_name = ? AND item_name = ?;""",(quantity,newBase,item_name))
            db.commit()
            return redirect(url_for('base_details', base_name=base_name))  

    
    base = db.execute(""" SELECT * FROM bases WHERE base_name = ?;""", (base_name,)).fetchone()
    base_items = db.execute(""" SELECT * FROM storage WHERE base_name = ?;""", (base_name,)).fetchall()
    base_members = db.execute(""" SELECT * FROM members WHERE residence =?;""", (base_name,)).fetchall()
    #if the base contains no items
    if len(base_items) == 0:
        base_items = 0
    delete = False
    if base_items == 0 and len(base_members) == 0:
        delete = True

    return render_template("base_storage.html", title="Manage Base Storage", base=base, base_items=base_items, addform=addform, deleteform=deleteform, moveform=moveform, delete=delete)

@app.route("/members", methods=["GET","POST"])
@login_required
def members():
    form = MembersForm()
    members = None
    db = get_db()

    db = get_db()
    db.execute(""" UPDATE user_site_tracker SET members = members + 1 WHERE member_id = ?""",(g.id,))
    db.commit()

    #choices for searching for members
    baseList = db.execute(""" SELECT * FROM bases ORDER BY base_name;""").fetchall()
    for base in baseList:
        form.residence.choices.append(base["base_name"])
    form.residence.choices.append("Any")
    
    membersList = db.execute(""" SELECT * FROM members ORDER BY name;""").fetchall()
    for member in membersList:
        form.name.choices.append(member["name"])
    form.name.choices.append("Any")
    
    ranksList = db.execute(""" SELECT * FROM ranks ORDER BY rank;""").fetchall()
    for rank in ranksList:
        form.rank.choices.append(rank["rank"])
    form.rank.choices.append("Any")

    if g.rank_value < g.permission_level:
        form.order.choices.remove("Status")
        form.order.choices.remove("Joined")
        form.order.choices.remove("Member ID")
        form.order.choices.remove("Recent Login")
    
    last_login = None

    if form.validate_on_submit():

        name = form.name.data
        rank = form.rank.data
        residence = form.residence.data
        gender = form.gender.data
        status = form.status.data
        order = form.order.data
        
        if name == "Any":
            name = "%"
        if status == "Any":
            status = "%"
        if rank == "Any":
            rank = "%"
        if residence == "Any":
            residence = "%"
        if gender == "Any":
            gender = "%"
        #for order by
        if order == "Member ID":
            members = db.execute(""" SELECT * FROM members WHERE name LIKE ? AND status LIKE ? AND rank LIKE ? AND gender LIKE ? AND residence LIKE ? ORDER BY member_id;""", (name,status,rank,gender,residence)).fetchall()
        elif order == "Age":
            members = db.execute(""" SELECT * FROM members WHERE name LIKE ? AND status LIKE ? AND rank LIKE ? AND gender LIKE ? AND residence LIKE ? ORDER BY age;""", (name,status,rank,gender,residence)).fetchall()
        elif order == "Name":
            members = db.execute(""" SELECT * FROM members WHERE name LIKE ? AND status LIKE ? AND rank LIKE ? AND gender LIKE ? AND residence LIKE ? ORDER BY name;""", (name,status,rank,gender,residence)).fetchall() 
        elif order == "Level":
            members = db.execute(""" SELECT * FROM members WHERE name LIKE ? AND status LIKE ? AND rank LIKE ? AND gender LIKE ? AND residence LIKE ? ORDER BY level;""", (name,status,rank,gender,residence)).fetchall()     
        elif order == "Rank":
            members = db.execute(""" SELECT * FROM members WHERE name LIKE ? AND status LIKE ? AND rank LIKE ? AND gender LIKE ? AND residence LIKE ? ORDER BY rank;""", (name,status,rank,gender,residence)).fetchall()      
        elif order == "Residence":
            members = db.execute(""" SELECT * FROM members WHERE name LIKE ? AND status LIKE ? AND rank LIKE ? AND gender LIKE ? AND residence LIKE ? ORDER BY residence;""", (name,status,rank,gender,residence)).fetchall()  
        elif order == "Gender":
            members = db.execute(""" SELECT * FROM members WHERE name LIKE ? AND status LIKE ? AND rank LIKE ? AND gender LIKE ? AND residence LIKE ? ORDER BY gender;""", (name,status,rank,gender,residence)).fetchall()
        elif order == "Joined":
            members = db.execute(""" SELECT * FROM members WHERE name LIKE ? AND status LIKE ? AND rank LIKE ? AND gender LIKE ? AND residence LIKE ? ORDER BY joined;""", (name,status,rank,gender,residence)).fetchall() 
        elif order == "Recent Login":
            members = db.execute(""" SELECT * FROM members JOIN login ON members.name = login.user_name WHERE name LIKE ? AND status LIKE ? AND rank LIKE ? AND gender LIKE ? AND residence LIKE ? ORDER BY last_login DESC;""", (name,status,rank,gender,residence)).fetchall() 
        else:
            members = db.execute(""" SELECT * FROM members WHERE name LIKE ? AND status LIKE ? AND rank LIKE ? AND gender LIKE ? AND residence LIKE ? ORDER BY status;""", (name,status,rank,gender,residence)).fetchall()  
      
        if len(members) == 0:
            members = 0

        last_login = {}
        #if there are members in the list then calculate their most recent login
        if members != 0:
            for member in members:
                last_log = db.execute(""" SELECT * FROM login WHERE user_name = ?;""", (member["name"],)).fetchone()
                date1 = datetime.strptime(last_log["last_login"], "%Y-%m-%d-%H-%M-%S")
                date2 = datetime.strptime(datetime.now().strftime("%Y-%m-%d-%H-%M-%S"), "%Y-%m-%d-%H-%M-%S")
                
                interval = int((date2 - date1).total_seconds())

                if interval >= 631139040:
                    interval = "Never"
                elif interval >= 31536000:
                    interval = (date2 - date1).days // 365
                    if interval == 1:
                        interval = str(interval) + " year ago"    
                    else:                  
                        interval = str(interval) + " years ago"
                elif interval >= 2628288:
                    interval = (date2 - date1).days // 30
                    if interval == 1:
                        interval = str(interval) + " month ago"    
                    else:                  
                        interval = str(interval) + " months ago"
                elif interval >= 604800:
                    interval = (date2 - date1).days // 7
                    if interval == 1:
                        interval = str(interval) + " week ago"    
                    else:                  
                        interval = str(interval) + " weeks ago"
                elif interval >= 86400:
                    interval = (date2 - date1).days
                    if interval == 1:
                        interval = str(interval) + " day ago"    
                    else:                  
                        interval = str(interval) + " days ago"                         
                elif interval >= 3600:
                    interval = interval // 3600
                    if interval == 1:
                        interval = str(interval) + " hour ago"    
                    else:                  
                        interval = str(interval) + " hours ago"
                elif interval >= 60:
                    interval = interval // 60
                    if interval == 1:
                        interval = str(interval) + " minute ago"    
                    else:                  
                        interval = str(interval) + " minutes ago" 
                else:
                    if interval == 1:
                        interval = str(interval) + " second ago"    
                    else:                  
                        interval = str(interval) + " seconds ago"                                   

                last_login[member["name"]] = interval

    return render_template("members.html", title="Members Page", members=members ,form=form, last_login=last_login)

@app.route("/applications", methods=["GET","POST"])
@login_required
def applications():
    form = ApplicationForm()
    db = get_db()

    if g.rank_value < g.permission_level:
        page = "Applications"
        return render_template("access_denier.html", required_rank=g.permission_rank ,page=page, title="Access Denied")

    db = get_db()
    db.execute(""" UPDATE user_site_tracker SET applications = applications + 1 WHERE member_id = ?""",(g.id,))
    db.commit()

    #list of applications
    applications = db.execute(""" SELECT * FROM applications""").fetchall()
    if form.validate_on_submit():
        #if clear is pressed removes all applications
        applications = db.execute(""" DELETE FROM applications""")
        db.commit()
        return redirect(url_for("applications"))
    return render_template("applications.html", title="Applications Page", applications=applications, form=form)

@app.route("/register", methods=["GET","POST"])
def register():
    form = RegistrationForm()
    for level in range(1,101):
        form.level.choices.append(level)

    if form.validate_on_submit():
        user_name = form.user_name.data
        user_name = user_name.lower()
        user_name = user_name.title()
        password = form.password.data
        password2 = form.password2.data
        age = form.age.data
        gender = form.gender.data
        email = form.email.data
        level = form.level.data
        db = get_db()
        
        #checking for clashing names from members and applications and email from login and applications
        possible_clashing_user = db.execute(""" SELECT * FROM members WHERE name=?;""",(user_name,)).fetchone()
        possible_clashing_user2 = db.execute(""" SELECT * FROM applications WHERE name=?;""",(user_name,)).fetchone()
        possible_clashing_emails = db.execute(""" SELECT * FROM applications WHERE email=?;""",(email,)).fetchone()
        possible_clashing_emails2 = db.execute(""" SELECT * FROM login WHERE email=?;""",(email,)).fetchone()
        
        #checking if name only contains characters
        if not user_name.isalpha():
            form.user_name.errors.append("Cannot contain numbers or special symbols")  

        elif possible_clashing_user is not None or possible_clashing_user2 is not None:
            form.user_name.errors.append("Username already taken!")
        
        elif possible_clashing_emails is not None or possible_clashing_emails2 is not None:
            form.email.errors.append("Email already taken!")
        
        else:
            application_date = datetime.now().strftime("%Y-%m-%d")
            db.execute(""" INSERT INTO applications (name,password,age,gender,level,application_date,email) VALUES (?,?,?,?,?,?,?);""", 
                       (user_name, generate_password_hash(password),age,gender,level,application_date,email))
            db.commit()
            return render_template("register.html", form=form, reply="Your application is pending. Please check your email.", title="Registration")
    
    return render_template("register.html", form=form, reply="", title="Registration")

@app.route("/login", methods=["GET","POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user_name = form.user_name.data
        user_name = user_name.lower()
        user_name = user_name.title()
        password = form.password.data
        db = get_db()
        possible_clashing_user = db.execute(""" SELECT * FROM login WHERE user_name=?;""",(user_name,)).fetchone()
        if possible_clashing_user is None:
            form.user_name.errors.append("No such users!")
        elif not check_password_hash(possible_clashing_user["password"], password):
            form.password.errors.append("Incorrect password!")
        else:
            session.clear()
            session["user_name"] = user_name
            db = get_db()
            user_data = db.execute(""" SELECT * FROM members WHERE name=?""",(user_name,)).fetchone()
            session["user_rank"] = user_data["rank"]
            rank_data = db.execute(""" SELECT * FROM ranks WHERE rank=?""", (user_data["rank"],)).fetchone()
            session["user_rank_value"] = rank_data["rank_value"]
            session["user_residence"] = user_data["residence"]
            session["user_id"] = user_data["member_id"]
            db.execute(""" UPDATE login SET last_login = ? WHERE user_name = ?;""", (datetime.now().strftime("%Y-%m-%d-%H-%M-%S"),user_name))
            db.commit()
            next_page = request.args.get("next")
            if not next_page:
                next_page = url_for("home")
            #giving cookie to user which logs when out in 2 days
            response = make_response(redirect(next_page))
            response.set_cookie("time","1", max_age=172800)
            return response
    return render_template("login.html", form=form, title="Log in")

@app.route("/logout")
def logout():
    session.clear()
    return redirect( url_for("home"))

@app.route("/forgot_password", methods=["GET","POST"])
def forgot_password():
    db = get_db()
    form = ForgotPasswordForm()

    if form.validate_on_submit():
        email = form.email.data
        
        email_check = db.execute(""" SELECT * FROM login WHERE email = ?;""", (email,)).fetchone()

        #check if the email is in the database
        if email_check is None:
            form.email.errors.append("No email found.")
        else:
            return render_template("forgot_password.html", title="Forgot Password", form=form, reply="Please check your email to change password.")
        

    return render_template("forgot_password.html", title="Forgot Password", form=form, reply="")
    
@app.route("/accept_member/<user_name>", methods=["POST","GET"])
@login_required
def accept_members(user_name):
    db = get_db()

    if g.rank_value < g.permission_level:
        page = "Page"
        return render_template("access_denier.html", required_rank=g.permission_rank ,page=page, title="Access Denied")
    
    applicant_details = db.execute(""" SELECT * FROM applications WHERE name =?;""", (user_name,)).fetchone()
    form = AcceptApplicantForm()

    baseList = db.execute(""" SELECT * FROM bases ORDER BY base_name;""").fetchall()
    for base in baseList:
        form.residence.choices.append(base["base_name"])

    if form.validate_on_submit():
        rank = form.rank.data
        residence = form.residence.data
        clashing = db.execute(""" SELECT * FROM login WHERE user_name=?""",(applicant_details["name"],)).fetchone()
        if clashing is None:
            joined = datetime.now().strftime("%Y-%m-%d")
            db.execute(""" INSERT INTO login (user_name,password,email,last_login) VALUES (?,?,?,?);""", (applicant_details["name"],applicant_details["password"],applicant_details["email"],"2000-01-01-00-00-00"))
            db.execute(""" INSERT INTO members (name,status,rank,age,gender,level,power_level,residence,contribution_points,joined) VALUES (?,?,?,?,?,?,?,?,?,?)""",
                        (applicant_details["name"],"Active",rank,applicant_details["age"],applicant_details["gender"],applicant_details["level"],getPowerLevel(applicant_details["level"]),residence,0,joined))
            db.execute(""" DELETE FROM applications WHERE name=?;""",(user_name,))
            db.commit()
            member_id = db.execute(""" SELECT * FROM members WHERE name =?""", (applicant_details["name"],)).fetchone()
            db.execute(""" INSERT INTO user_site_tracker (member_id,home,profile,members,bases,applications,missions,rankings) VALUES
                        (?,?,?,?,?,?,?,?)""", (member_id["member_id"],0,0,0,0,0,0,0))
            db.execute(""" INSERT INTO pfp (member_id,picture) VALUES (?,?)""", (member_id["member_id"],"default.jfif"))
            db.commit()
            return redirect( url_for("applications"))
    return render_template("applicant.html", applicant_details=applicant_details, form=form,title="Accept Applicant")

@app.route("/decline_member/<user_name>")
@login_required
def decline_members(user_name):
    db = get_db()

    if g.rank_value < g.permission_level:
        page = "Page"
        return render_template("access_denier.html", required_rank=g.permission_rank ,page=page, title="Access Denied")
    
    db.execute(""" DELETE FROM applications WHERE name=?;""",(user_name,))
    db.commit()
    return redirect(url_for("applications"))

@app.route("/remove_member/<name>/<same_base>")
@login_required
def remove_member(name,same_base):
    db = get_db()

    if g.rank_value < g.permission_level:
        page = "Page"
        return render_template("access_denier.html", required_rank=g.permission_rank ,page=page, title="Access Denied")
    
    if same_base == True:
        return redirect(url_for("members"))
    
    name_rank = db.execute(""" SELECT * FROM members WHERE name = ? ;""", (name,)).fetchone()
    rank_value = db.execute(""" SELECT * FROM ranks WHERE rank = ? ;""", (name_rank["rank"],)).fetchone()
    if g.rank_value <= int(rank_value["rank_value"]):
        return redirect(url_for("members"))
    
    #remove member from members database, adds into former members database, removes from missions which are not complete and removes from login
    member_details = db.execute(""" SELECT * FROM members WHERE name =? ;""", (name,)).fetchone()

    db.execute(""" INSERT INTO former_members (member_id,name,status,rank,age,gender,level,power_level,residence,contribution_points,joined,kicked)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?);""", (member_details["member_id"], member_details["name"], member_details["status"], member_details["rank"]
                , member_details["age"], member_details["gender"], member_details["level"], member_details["power_level"]
                , member_details["residence"], member_details["contribution_points"], member_details["joined"],datetime.now().strftime("%Y-%m-%d")))
    
    db.execute(""" DELETE FROM members WHERE name = ?;""", (name,))
    db.execute(""" DELETE FROM login WHERE user_name = ?;""", (name,))
    db.commit()
    users_missions = db.execute(""" SELECT * FROM mission_management JOIN missions ON mission_management.mission_id = missions.mission_id 
                WHERE member_id = ? AND (missions.mission_status = "Incomplete" OR missions.mission_status = "Closed") ;""", (member_details["member_id"],)).fetchall()
    for mission in users_missions:
        db.execute(""" UPDATE missions SET current_party_number = current_party_number -1 WHERE mission_id=? ;""", (mission["mission_id"],))
        db.execute(""" DELETE FROM mission_management WHERE mission_id =? and member_id=? ;""", (mission["mission_id"],member_details["member_id"]))
        db.commit()
    return redirect(url_for("members"))

@app.route("/modify/<user_name>", methods=["GET","POST"])
@login_required
def modify_member(user_name):
    form = ModifyMemberDetailsForm()
    db = get_db()

    if g.rank_value < g.permission_level:
        page = "Page"
        return render_template("access_denier.html", required_rank=g.permission_rank ,page=page, title="Access Denied")

    baseList = db.execute(""" SELECT * FROM bases ORDER BY base_name;""").fetchall()
    for base in baseList:
        form.residence.choices.append(base["base_name"])

    user_details = db.execute(""" SELECT * FROM members WHERE name = ?;""", (user_name,)).fetchone()
    user_rank_value = db.execute(""" SELECT * FROM ranks WHERE rank = ?;""", (user_details["rank"],)).fetchone()
    rank_options = db.execute(""" SELECT * FROM ranks WHERE rank_value < ? ORDER BY rank;""", (g.rank_value,)).fetchall()
    for rank_option in rank_options:
        form.rank.choices.append(rank_option["rank"])

    for level in range(1,101):
        form.level.choices.append(level)
 
    if g.rank == "Founder" and int(user_rank_value["rank_value"]) == 10:
        form.rank.choices = ["Founder"]
        form.level.choices = [100]
        form.status.choices = ["Active"]
    
    #set default values to their current values in the database
    form.status.default = "Active"
    form.rank.default = user_details["rank"]
    form.age.default = user_details["age"]
    form.level.default = int(user_details["level"])
    form.residence.default = user_details["residence"]

    same_base_checker = db.execute(""" SELECT * FROM members WHERE name = ?; """, (user_name,)).fetchone()
    user_base = db.execute(""" SELECT * FROM members WHERE name = ?; """, (g.user,)).fetchone()
    same_base = False
    if same_base_checker["residence"] == user_base["residence"]:
        same_base = True

    user_picture = db.execute(""" SELECT * FROM pfp WHERE member_id = ?;""", (user_details["member_id"],)).fetchone()
    picture = user_picture["picture"]

    if form.validate_on_submit():
        residence = form.residence.data
        status = form.status.data
        rank = form.rank.data
        age = int(form.age.data)
        level = int(form.level.data)

        #makes sure that founder rank cannot demote or delevel themselves
        if g.rank == "Founder" and int(user_rank_value["rank_value"]) == 10:
            status = "Active"
            rank = "Founder"
            level = 100

        
        db.execute(""" UPDATE members SET status = ?, rank = ?, residence = ?, age = ?, level = ?, power_level = ? WHERE name = ?;""", (status,rank,residence,age,level,getPowerLevel(level),user_name))
        db.commit()
        return redirect(url_for('modify_member', user_name=user_name))
    form.process()
    return render_template("modify_member.html", user_details=user_details, form=form, user_rank_value=user_rank_value, title="Modify Member", same_base = same_base, picture=picture)

@app.route("/item_archive", methods=["GET","POST"])
@login_required
def item_archive():
    form = ItemArchiveForm()
    item_archive_list = None
    db = get_db()

    if g.rank_value < g.permission_level:
        page = "Page"
        return render_template("access_denier.html", required_rank=g.permission_rank ,page=page, title="Access Denied")

    #adds all items in the database to choices  
    itemsList = db.execute(""" SELECT * FROM items ORDER BY item_name;""").fetchall()
    for item in itemsList:
        form.item_name.choices.append(item["item_name"])
    form.item_name.choices.append("Any")

    #adds all rarities in the database to choices
    rarityList = db.execute(""" SELECT * FROM rarity ORDER BY rarity;""").fetchall()
    for rarity in rarityList:
        form.item_rarity.choices.append(rarity["rarity"])
    form.item_rarity.choices.append("Any")

    
    if form.validate_on_submit():
        item_name = form.item_name.data
        item_rarity = form.item_rarity.data

        if item_name == "Any":
            item_name = "%"
        if item_rarity == "Any":
            item_rarity = "%"
        
        item_archive_list = db.execute(""" SELECT * FROM items WHERE item_name LIKE ? AND rarity LIKE ?;""", (item_name,item_rarity)).fetchall()

        if len(item_archive_list) == 0:
            item_archive_list = 0
    return render_template("item_archive.html", form=form, title="Item Archive", item_archive_list=item_archive_list)

@app.route("/add_to_item_archive",methods=["GET","POST"])
@login_required
def add_to_item_archive():
    form = AddToItemArchiveForm()
    db = get_db()

    if g.rank_value < g.permission_level:
        page = "Page"
        return render_template("access_denier.html", required_rank=g.permission_rank ,page=page, title="Access Denied")
    
    rarityList = db.execute(""" SELECT * FROM rarity ORDER BY rarity;""").fetchall()
    for rarity in rarityList:
        form.item_rarity.choices.append(rarity["rarity"])

    
    if form.validate_on_submit():
        item_name = form.item_name.data
        item_rarity = form.item_rarity.data
        item_description = form.item_description.data

        item_name = wordFilter(item_name)

        #check if item is already in item archive
        clashing_item = db.execute(""" SELECT * FROM items WHERE item_name = ?;""", (item_name,)).fetchone()
        if clashing_item != None:
            form.item_name.errors.append("Item is already in the Item Archive")
        
        else:
            db.execute(""" INSERT INTO items (item_name,rarity,item_description) VALUES (?,?,?);""", (item_name,item_rarity,item_description))
            db.commit()
            return redirect(url_for('item_archive'))
    return render_template("add_to_item_archive.html", form=form, title="Add New Items To Archive")

@app.route("/remove_item_from_item_archive/<item_name>")
@login_required
def remove_item_from_item_archive(item_name):
    db = get_db()

    if g.rank_value < g.permission_level:
        page = "Page"
        return render_template("access_denier.html", required_rank=g.permission_rank ,page=page, title="Access Denied")
    
    db.execute(""" DELETE FROM items WHERE item_name = ?;""", (item_name,))
    db.commit()
    return redirect(url_for('item_archive'))

@app.route("/add_new_base", methods=["GET","POST"])
@login_required
def add_new_base():
    db = get_db()

    if g.rank_value < 10:
        page = "Page"
        return render_template("access_denier.html", required_rank=g.permission_rank ,page=page, title="Access Denied")
    
    form = AddNewBaseForm()

    if form.validate_on_submit():
        base_name = form.base_name.data
        base_location = form.base_location.data

        base_name = wordFilter(base_name)
        
        clashing_base_name = db.execute(""" SELECT * FROM bases WHERE base_name = ?;""", (base_name,)).fetchone()
        
        if clashing_base_name is not None:
            form.base_name.errors.append("Base already exists")
        
        else:
            db.execute(""" INSERT INTO bases (base_name,location) VALUES (?,?);""", (base_name,base_location))
            db.commit()
            return redirect(url_for('bases'))
        
    return render_template("add_new_base.html", form=form)

@app.route("/remove_base/<base_name>")
@login_required
def remove_base(base_name):
    db = get_db()

    if g.rank_value < 10:
        page = "Page"
        return render_template("access_denier.html", required_rank="Founder" ,page=page, title="Access Denied")

    base_items_checker = db.execute(""" SELECT * FROM storage WHERE base_name = ?;""", (base_name,)).fetchone()
    base_members_checker = db.execute(""" SELECT * FROM members WHERE residence =?;""", (base_name,)).fetchone()
    if base_items_checker is None and base_members_checker is None:
        db.execute(""" DELETE FROM bases WHERE base_name = ?;""", (base_name,))
        db.commit()
        return redirect(url_for("bases"))
    else:
        return redirect(url_for("bases"))

@app.route("/missions", methods=["GET","POST"])
@login_required
def missions():
    db = get_db()

    db = get_db()
    db.execute(""" UPDATE user_site_tracker SET missions = missions + 1 WHERE member_id = ?""",(g.id,))
    db.commit()

    form = MissionSearchingForm()
    missions_list = None
    
    missions = db.execute(""" SELECT * FROM missions WHERE mission_status = "Incomplete" ORDER BY mission_id;""").fetchall()

    for mission_id in missions: 
        form.mission_id.choices.append(mission_id["mission_id"])
    form.mission_id.choices.append("Any")

    if form.validate_on_submit():
        difficulty = form.difficulty.data
        rank_requirement = form.rank_requirement.data
        mission_id = form.mission_id.data
        mission_status = form.mission_status.data
        status1 = "Incomplete"
        status2 = "Closed"

        #filter for mission checking
        if difficulty == "Any":
            difficulty = "%"
        if rank_requirement == "Any":
            rank_requirement = "%"
        if mission_id == "Any":
            mission_id = "%"
        if mission_status == "Incomplete":
            status1 = "Incomplete"
            status2 = "Incomplete"
        elif mission_status == "Closed":
            status1 = "Closed"
            status2 = "Closed"

        missions_list = db.execute(""" SELECT * FROM missions WHERE (mission_status LIKE ? OR mission_status LIKE ?) AND mission_level LIKE ? AND rank_requirement LIKE ? AND mission_id LIKE ?;"""
                                   , (status1, status2, difficulty,rank_requirement,mission_id)).fetchall()

        if len(missions_list) == 0:
            missions_list = 1
    return render_template("missions.html", missions_list=missions_list, title="Missions", form=form)

@app.route("/add_mission", methods=["GET","POST"])
@login_required
def add_mission():
    form = AddMissionForm()
    db = get_db()

    if g.rank_value < g.permission_level:
        page = "Page"
        return render_template("access_denier.html", required_rank=g.permission_rank ,page=page, title="Access Denied")



    if form.validate_on_submit():
        mission_name = form.mission_name.data
        mission_description = form.mission_description.data
        mission_party_limit = form.mission_party_limit.data
        rank_requirement = form.rank_requirement.data
        mission_level = form.mission_level.data
        mission_reward = form.mission_reward.data

        mission_name = wordFilter(mission_name)
         
        db.execute(""" INSERT INTO missions (mission_name, mission_level, rank_requirement, mission_reward, current_party_number, max_party_number, mission_description, mission_status) 
                    VALUES (?,?,?,?,?,?,?,?);""", (mission_name, mission_level, rank_requirement, mission_reward, 0, mission_party_limit, mission_description,"Incomplete"))
        db.commit()
        return redirect(url_for("missions"))
    return render_template("add_mission.html", form=form)

@app.route("/mission_details/<mission_id>", methods=["GET","POST"])
@login_required
def mission_details(mission_id):
    db = get_db()
    form = AcceptMissionForm()

    mission_details = db.execute(""" SELECT * FROM missions WHERE mission_id = ?;""", (mission_id,)).fetchone()
    ranks = db.execute(""" SELECT * FROM ranks;""").fetchall()
    same_checker = db.execute(""" SELECT * FROM mission_management WHERE mission_id =? AND member_id = ?;""", (mission_id,g.id)).fetchone()

    #checks the missions party members
    party_members_list = db.execute(""" SELECT * FROM mission_management WHERE mission_id = ? ORDER BY member_id;""", (mission_id,)).fetchall()
    party_members = []
    for member in party_members_list:
        member_details = db.execute(""" SELECT * FROM members WHERE member_id = ?;""", (member["member_id"],)).fetchone()
        party_members.append(member_details)

    mission_rank_value = 0
    for rank in ranks:
        if rank["rank"] == mission_details["rank_requirement"]:
            mission_rank_value = int(rank["rank_value"])
    
    if form.validate_on_submit():
        #sees whether the user is already in the party to change accept and leave
        same_checker = db.execute(""" SELECT * FROM mission_management WHERE mission_id =? AND member_id = ?;""", (mission_id,g.id)).fetchone()
        if same_checker is not None:
            return redirect(url_for("leave_mission", mission_id=mission_id))
 
        if g.rank_value < mission_rank_value:
            form.submit.errors.append("Rank Too Low")
        elif int(mission_details["current_party_number"]) == int(mission_details["max_party_number"]):
            form.submit.errors.append("Max Party Number Reached")
        else:
            db.execute(""" UPDATE missions SET current_party_number = current_party_number + 1 WHERE mission_id = ?;""", (mission_id,))
            db.execute(""" INSERT INTO mission_management (mission_id,mission_name,member_id) VALUES (?,?,?);""", (mission_id,mission_details["mission_name"],g.id))
            db.commit()
            return redirect(url_for("mission_details", mission_id=mission_id))

    if same_checker is not None:
        same_checker = 0
        form.submit.label.text = "Leave"

    return render_template("mission_details.html", title ="Accept Mission", mission_details=mission_details, form=form, party_members=party_members)

@app.route("/leave_mission/<mission_id>")
@login_required
def leave_mission(mission_id):
        db = get_db()
        #check if mission has status Incomplete
        mission_status = db.execute(""" SELECT * FROM missions WHERE mission_id = ? AND mission_status = "Incomplete" """, (mission_id,)).fetchone()
        if mission_status is None:
            return redirect(url_for("missions"))
        db.execute(""" DELETE FROM mission_management WHERE mission_id = ? and member_id = ? ;""", (mission_id,g.id))
        db.execute(""" UPDATE missions SET current_party_number = current_party_number - 1 WHERE mission_id = ?;""", (mission_id,))
        db.commit()
        return redirect(url_for("mission_details", mission_id = mission_id ))
    
@app.route("/remove_mission/<mission_id>")
@login_required
def remove_mission(mission_id):
    db = get_db()

    if g.rank_value < g.permission_level:
        page = "Page"
        return render_template("access_denier.html", required_rank=g.permission_rank ,page=page, title="Access Denied")

    db.execute(""" DELETE FROM mission_management WHERE mission_id = ?;""", (mission_id,))
    db.execute(""" DELETE FROM missions WHERE mission_id = ? ;""", (mission_id,))
    db.commit()
    return redirect(url_for("missions"))

@app.route("/mark_mission_as_complete/<mission_id>")
@login_required
def mission_complete(mission_id):
    db = get_db()

    if g.rank_value < g.permission_level:
        page = "Page"
        return render_template("access_denier.html", required_rank=g.permission_rank ,page=page, title="Access Denied")

    #check if the mission status is closed
    mission_status = db.execute(""" SELECT * FROM missions WHERE mission_id = ? AND mission_status = "Closed" ;""",(mission_id,)).fetchone()
    if mission_status is None:
        return redirect(url_for("missions"))

    mission_party_checker = db.execute(""" SELECT * FROM missions WHERE mission_id = ? ;""", (mission_id,)).fetchone()
    if int(mission_party_checker["current_party_number"]) == 0:
        return redirect(url_for("mission_details", mission_id=mission_id))

    db.execute(""" UPDATE missions SET mission_status = "Complete" WHERE mission_id = ? ;""", (mission_id,))
    party_members = db.execute(""" SELECT * FROM mission_management WHERE mission_id = ? ;""", (mission_id,)).fetchall()
    mission = db.execute(""" SELECT * FROM missions WHERE mission_id = ? ;""", (mission_id,)).fetchone()

    #giving contribution points to party members
    for member in party_members:
        db.execute(""" UPDATE members SET contribution_points = contribution_points + ? WHERE member_id = ? ;""", (mission["mission_reward"],member["member_id"]))
        db.commit()

    return redirect (url_for("missions"))

@app.route("/close_mission/<mission_id>")
@login_required
def close_mission(mission_id):
    db = get_db()

    if g.rank_value < g.permission_level:
        page = "Page"
        return render_template("access_denier.html", required_rank=g.permission_rank ,page=page, title="Access Denied")
    
    db.execute(""" UPDATE missions SET mission_status="Closed" WHERE mission_id = ?;""", (mission_id,))
    db.commit()
    return redirect(url_for("mission_details", mission_id=mission_id))
    
@app.route("/completed_missions")
@login_required
def completed_missions():
    db = get_db()

    if g.rank_value < g.permission_level:
        page = "Page"
        return render_template("access_denier.html", required_rank=g.permission_rank ,page=page, title="Access Denied")
    
    completed_missions = db.execute(""" SELECT * FROM missions WHERE mission_status = "Complete" ORDER BY mission_id;""").fetchall()

    total_contribution_points = {}
    for mission in completed_missions:
        contribution_points_recorder = int(mission["current_party_number"]) * int(mission["mission_reward"])
        total_contribution_points[mission["mission_id"]] = contribution_points_recorder


    return render_template("completed_missions.html", completed_missions=completed_missions, total_contribution_points=total_contribution_points, title="Completed Missions")

@app.route("/completed_mission_party/<mission_id>")
@login_required
def completed_mission_party(mission_id):
    db = get_db()

    if g.rank_value < g.permission_level:
        page = "Page"
        return render_template("access_denier.html", required_rank=g.permission_rank ,page=page, title="Access Denied")

    party_members_list = db.execute(""" SELECT * FROM mission_management WHERE mission_id = ? ORDER BY member_id;""", (mission_id,)).fetchall()
    
    #list of party members who are still a member of the organisation and not
    party_members_current = []
    party_members_former = []

    for member in party_members_list:
        member_details = db.execute(""" SELECT * FROM members WHERE member_id = ?;""", (member["member_id"],)).fetchone()
        if member_details is not None:
            party_members_current.append(member_details)
        else:
            former_member_details = db.execute(""" SELECT * FROM former_members WHERE member_id =?;""", (member["member_id"],)).fetchone()
            party_members_former.append(former_member_details)
    
    if party_members_current == []:
        party_members_current = None
    
    if party_members_former == []:
        party_members_former = None

    return render_template("completed_mission_party.html", party_members_current=party_members_current, title="Party Members", party_members_former=party_members_former)

@app.route("/permissions")
@login_required
def permissions():
    db = get_db()

    if g.rank_value < 10:
        page = "Page"
        return render_template("access_denier.html", required_rank=g.permission_rank ,page=page, title="Access Denied")
    
    permissions = db.execute(""" SELECT * FROM permissions;""").fetchall()
    
    return render_template("/permissions.html", title="Permissions", permissions=permissions)

@app.route("/change_permission/<permission_id>", methods=["GET","POST"])
@login_required
def change_permission(permission_id):
    db = get_db()

    if g.rank_value < 10:
        page = "Page"
        return render_template("access_denier.html", required_rank=g.permission_rank ,page=page, title="Access Denied")
    
    form = PermissionForm()
    permission = db.execute(""" SELECT * FROM permissions WHERE permission_id = ?;""", (permission_id,)).fetchone()

    ranksList = db.execute(""" SELECT * FROM ranks ORDER BY rank;""").fetchall()
    for rank in ranksList:
        form.new_permission_rank.choices.append(rank["rank"])

    if form.validate_on_submit():
        new_permission_rank = form.new_permission_rank.data
    
        db.execute(""" UPDATE permissions SET permission_rank = ? WHERE permission_id = ?;""", 
                (new_permission_rank, permission_id))
        db.commit()
        return redirect(url_for('change_permission', permission_id=permission_id))

    form.process()
    return render_template("change_permission.html", title="Change Permission", permission=permission, form=form)

@app.route("/rankings")
@login_required
def rankings():
    db = get_db()

    db = get_db()
    db.execute(""" UPDATE user_site_tracker SET rankings = rankings + 1 WHERE member_id = ?""",(g.id,))
    db.commit()

    bases = db.execute(""" SELECT * FROM bases;""").fetchall()
    base_power_levels = {}

    #adds up all the bases powers and picks the 10 strongest ones
    for base in bases:
        power_recorder = 0
        people = db.execute(""" SELECT * FROM members WHERE residence = ?;""", (base["base_name"],)).fetchall()
        if people is None:
            base_power_levels.append(0)
        else:
            for person in people:
                power_recorder += int(person["power_level"])
        base_power_levels[base["base_name"]] = power_recorder
    
    #ordering ranks of bases
    top_10_bases = baseRanking(base_power_levels)
    top_10_rankings = {}
    top_10_bases_location = {}
    rank_counter = 0

    for base in top_10_bases:
        rank_counter +=1
        base_details = db.execute(""" SELECT * FROM bases WHERE base_name = ?;""", (base,)).fetchone()
        top_10_bases_location[base_details["base_name"]] = base_details["location"]
        top_10_rankings[base] = rank_counter 
    
    branch_head_ranking = db.execute(""" SELECT * FROM members WHERE rank = "Branch Head" ORDER BY power_level DESC LIMIT 10;""").fetchall()
    core_member_ranking = db.execute(""" SELECT * FROM members WHERE rank = "Core Member" ORDER BY power_level DESC LIMIT 100;""").fetchall()
    inner_member_ranking = db.execute(""" SELECT * FROM members WHERE rank = "Inner Member" ORDER BY power_level DESC LIMIT 100;""").fetchall()
    outer_member_ranking = db.execute(""" SELECT * FROM members WHERE rank = "Outer Member" ORDER BY power_level DESC LIMIT 100;""").fetchall() 

    return render_template("rankings.html", title="Rankings", top_10_bases=top_10_bases, top_10_rankings=top_10_rankings, core_member_ranking=core_member_ranking,
                           inner_member_ranking=inner_member_ranking, outer_member_ranking=outer_member_ranking, top_10_bases_location=top_10_bases_location,
                           branch_head_ranking=branch_head_ranking)

@app.errorhandler(404)
def not_found(e):
    return render_template("error_handler.html", error="404 Page Not Found")

