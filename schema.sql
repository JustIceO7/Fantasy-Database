DROP TABLE IF EXISTS members;

CREATE TABLE members
(
    member_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(20) NOT NULL,
    status VARCHAR(1) NOT NULL,
    rank VARCHAR(20) NOT NULL,
    age INTEGER NOT NULL,
    gender CHAR(10) NOT NULL,
    level INTEGER NOT NULL,
    power_level INTEGER NOT NULL,
    residence VARCHAR(40) NOT NULL,
    contribution_points INTEGER NOT NULL,
    joined DATE NOT NULL

);

INSERT INTO members (name,status,rank,age,gender,level,power_level,residence,contribution_points,joined)
VALUES
    ('Oya','Active','Founder',200,'Male',100,6930000,'Cloud Heavenly Palace',999999999,'2020-12-20'),
    ('Stella','Active','Branch Head',120,'Female',95,1520000,'Frozen Palace',999999999,'2020-12-20'),
    ('Roam','Active','Branch Head',100,'Male',85,1101600,'Earthern Dome',999999999,'2020-12-20'),
    ('Emilia','Active','Branch Head',80,'Female',80,979200,'Misty Peaks',999999999,'2020-12-20'),
    ('Rose','Active','Branch Head', 160,'Female',90,1368000,'Smelting Mountains',999999999,'2020-12-20');





DROP TABLE IF EXISTS former_members;

CREATE TABLE former_members
(
    member_id INTEGER PRIMARY KEY,
    name VARCHAR(20) NOT NULL,
    status VARCHAR(1) NOT NULL,
    rank VARCHAR(20) NOT NULL,
    age INTEGER NOT NULL,
    gender CHAR(10) NOT NULL,
    level INTEGER NOT NULL,
    power_level INTEGER NOT NULL,
    residence VARCHAR(40) NOT NULL,
    contribution_points INTEGER NOT NULL,
    joined DATE NOT NULL,
    kicked DATE NOT NULL

);





DROP TABLE IF EXISTS ranks;

CREATE TABLE ranks
(
    rank VARCHAR(20) PRIMARY KEY NOT NULL,
    rank_value INTEGER NOT NULL
);

INSERT INTO ranks (rank,rank_value)
VALUES
    ('Founder',10),
    ('Branch Head',8),
    ('Core Member',3),
    ('Inner Member',2),
    ('Outer Member',1);




DROP TABLE IF EXISTS bases;

CREATE TABLE bases
(
    base_id INTEGER PRIMARY KEY AUTOINCREMENT,
    base_name VARCHAR(20) NOT NULL,
    location VARCHAR(20) NOT NULL

);

INSERT INTO bases (base_name,location)
VALUES
    ('Cloud Heavenly Palace','Central'),
    ('Frozen Palace', 'North'),
    ('Earthern Dome', 'East'),
    ('Misty Peaks', 'South'),
    ('Smelting Mountains', 'West');




DROP TABLE IF EXISTS storage;

CREATE TABLE storage
(
    base_name VARCHAR(40) NOT NULL,
    item_name VARCHAR(20) NOT NULL,
    item_rarity VARCHAR(20) NOT NULL,
    quantity INTEGER
);

INSERT INTO storage (base_name,item_name,item_rarity,quantity)
VALUES
    ('Cloud Heavenly Palace','Metal','Uncommon',20000),
    ('Cloud Heavenly Palace','Gold Coins','Common',100000000),
    ('Cloud Heavenly Palace','Wood','Common',600000),
    ('Cloud Heavenly Palace','Inferno Stone','Rare',2000),
    ('Cloud Heavenly Palace','Frost Stone','Rare',400),
    ('Cloud Heavenly Palace','Aqua Stone','Rare',1800),
    ('Cloud Heavenly Palace','Life Stone','Rare',1000),
    ('Cloud Heavenly Palace','Dragon Egg','Legendary',1),

    ('Frozen Palace','Metal','Uncommon',6000),
    ('Frozen Palace','Gold Coins','Common',50000000),
    ('Frozen Palace','Wood','Common',200000),
    ('Frozen Palace','Frost Stone','Rare',200),

    ('Earthern Dome','Metal','Uncommon',12000),
    ('Earthern Dome','Gold Coins','Common',90000000),
    ('Earthern Dome','Wood','Common',80000),
    ('Earthern Dome','Life Stone','Rare',200),

    ('Misty Peaks','Metal','Uncommon',4000),
    ('Misty Peaks','Gold Coins','Common',60000000),
    ('Misty Peaks','Wood','Common',400000),
    ('Misty Peaks','Aqua Stone','Rare',1000),

    ('Smelting Mountains','Metal','Uncommon',8000),
    ('Smelting Mountains','Gold Coins','Common',80000000),
    ('Smelting Mountains','Wood','Common',200000),
    ('Smelting Mountains','Inferno Stone','Rare',600);




DROP TABLE IF EXISTS items;

CREATE TABLE items
(
    item_name VARCHAR(20) PRIMARY KEY NOT NULL,
    rarity VARCHAR(20) NOT NULL,
    item_description TEXT NOT NULL
);

INSERT INTO items (item_name,rarity,item_description)
VALUES
    ('Gold Coins', 'Common','The worlds globally recognised currency.'),
    ('Metal', 'Uncommon','A hard rock,metal or stone?'),
    ('Wood', 'Common','From fresh trees.'),
    ('Inferno Stone', 'Rare','Rare stone from the middle of the volcano.'),
    ('Aqua Stone', 'Rare','Rare stone from the deepest depths of the ocean.'),
    ('Life Stone', 'Rare','Rare stone birth from mother nature.'),
    ('Frost Stone', 'Rare','Rare stone from the middle of giant icebergs.'),
    ('Dragon Egg', 'Legendary','Egg of a dragon.');




DROP TABLE IF EXISTS rarity;

CREATE TABLE rarity
(
    rarity VARCHAR(20) PRIMARY KEY
);

INSERT INTO rarity (rarity)
VALUES
    ('Common'),
    ('Uncommon'),
    ('Rare'),
    ('Legendary');




DROP TABLE IF EXISTS applications;

CREATE TABLE applications
(
    applicant_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(20) NOT NULL,
    age INTEGER NOT NULL,
    level INTERGER NOT NULL,
    password TEXT NOT NULL,
    email TEXT NOT NULL,
    gender CHAR(10) NOT NULL,
    application_date DATE NOT NULL

);




DROP TABLE IF EXISTS login;

CREATE TABLE login
(
    user_name TEXT PRIMARY KEY,
    password TEXT NOT NULL,
    email TEXT NOT NULL,
    last_login NOT NULL
);

INSERT INTO login (user_name,password,email,last_login)
VALUES
    ('Oya','pbkdf2:sha256:260000$aW3h1DrdzyYlXKOT$ffb752df3f5f2146622443d8a3fffc25e54870b7edb04b4148c844d864bcf6ff','777@gmail.com','2020-12-20-00-00-00'),
    ('Stella','pbkdf2:sha256:260000$aW3h1DrdzyYlXKOT$ffb752df3f5f2146622443d8a3fffc25e54870b7edb04b4148c844d864bcf6ff','666@gmail.com','2020-12-20-00-00-00'),
    ('Roam','pbkdf2:sha256:260000$aW3h1DrdzyYlXKOT$ffb752df3f5f2146622443d8a3fffc25e54870b7edb04b4148c844d864bcf6ff','555@gmail.com','2020-12-20-00-00-00'),
    ('Emilia','pbkdf2:sha256:260000$aW3h1DrdzyYlXKOT$ffb752df3f5f2146622443d8a3fffc25e54870b7edb04b4148c844d864bcf6ff','444@gmail.com','2020-12-20-00-00-00'),
    ('Rose','pbkdf2:sha256:260000$aW3h1DrdzyYlXKOT$ffb752df3f5f2146622443d8a3fffc25e54870b7edb04b4148c844d864bcf6ff','333@gmail.com','2020-12-20-00-00-00');




DROP TABLE IF EXISTS missions;

CREATE TABLE missions
(
    mission_id INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_name TEXT NOT NULL,
    mission_level TEXT NOT NULL,
    rank_requirement TEXT NOT NULL,
    current_party_number INTEGER NOT NULL,
    max_party_number INTEGER NOT NULL,
    mission_description TEXT NOT NULL,
    mission_reward INTEGER NOT NULL,
    mission_status TEXT NOT NULL
);




DROP TABLE IF EXISTS mission_management;

CREATE TABLE mission_management
(
    mission_id INTEGER,
    mission_name TEXT,
    member_id INTERGER
);




DROP TABLE IF EXISTS permissions;

CREATE TABLE permissions
(
    permission_id INTEGER PRIMARY KEY AUTOINCREMENT,
    permission_name TEXT NOT NULL,
    permission_rank TEXT NOT NULL
);

INSERT INTO permissions (permission_name,permission_rank)
VALUES
    ('Page Viewing', 'Branch Head');





DROP TABLE IF EXISTS user_site_tracker;

CREATE TABLE user_site_tracker
(
    member_id INTEGER PRIMARY KEY,
    home INTEGER,
    profile INTEGER,
    members INTEGER,
    bases INTEGER,
    applications INTEGER,
    missions INTEGER,
    rankings INTEGER
);

INSERT INTO user_site_tracker (member_id,home,profile,members,bases,applications,missions,rankings)
VALUES
    (1,0,0,0,0,0,0,0),
    (2,0,0,0,0,0,0,0),
    (3,0,0,0,0,0,0,0),
    (4,0,0,0,0,0,0,0),
    (5,0,0,0,0,0,0,0);




DROP TABLE IF EXISTS pfp;

CREATE TABLE pfp
(
    member_id INTEGER PRIMARY KEY,
    picture
);

INSERT INTO pfp (member_id,picture)
VALUES
    (1,'default.jfif'),
    (2,'default.jfif'),
    (3,'default.jfif'),
    (4,'default.jfif'),
    (5,'default.jfif');




SELECT * FROM members;
SELECT * FROM former_members;
SELECT * FROM bases;
SELECT * FROM storage;
SELECT * FROM applications;
SELECT * FROM login;
SELECT * FROM ranks;
SELECT * FROM items;
SELECT * FROM rarity;
SELECT * FROM missions;
SELECT * FROM mission_management;
SELECT * FROM permissions;
SELECT * FROM user_site_tracker;
SELECT * FROM pfp;