DROP TABLE IF EXISTS `appointment`;
DROP TABLE IF EXISTS `advisor`;
DROP TABLE IF EXISTS `student`;

CREATE TABLE advisor (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  email VARCHAR(255) NOT NULL,
  PRIMARY KEY  (id),
  UNIQUE KEY email (email)
)ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE student (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  email VARCHAR(255) NOT NULL,
  name VARCHAR(255) NOT NULL,
  PRIMARY KEY  (id),
  UNIQUE KEY email (email)
)ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE appointment (
  apt_date VARCHAR(255) NOT NULL,
  apt_time VARCHAR(255) NOT NULL,
  apt_uid VARCHAR(255) NOT NULL,
  aid INT UNSIGNED NOT NULL,
  sid INT UNSIGNED NOT NULL,
  PRIMARY KEY  (apt_uid),
  FOREIGN KEY (aid) REFERENCES advisor (id) ON UPDATE CASCADE,
  FOREIGN KEY (sid) REFERENCES student (id) ON UPDATE CASCADE
)ENGINE=InnoDB DEFAULT CHARSET=utf8;

INSERT INTO advisor(id, email)
VALUES (
    DEFAULT,
    "advisor1@oregonstate.edu"
);

INSERT INTO student(id, email, name)
VALUES (
    DEFAULT,
    "student1@oregonstate.edu",
    "Steve Steverson"
);

INSERT INTO appointment(apt_date, apt_time, apt_uid, aid, sid)
VALUES (
    "12-01-2014",
    "12:30am",
    "apt_uid-goes-here",
    (SELECT id FROM advisor WHERE email = "advisor1@oregonstate.edu"),
    (SELECT id FROM student WHERE name = "Steve Steverson")
);
