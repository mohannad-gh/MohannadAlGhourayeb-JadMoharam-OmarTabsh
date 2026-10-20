-- Actual SQLAlchemy table definitions from Mohannad models
CREATE TABLE users (
	id INTEGER NOT NULL,
	full_name VARCHAR(150) NOT NULL,
	username VARCHAR(80) NOT NULL,
	email VARCHAR(150) NOT NULL,
	password_hash VARCHAR(255) NOT NULL,
	department VARCHAR(100) NOT NULL,
	role VARCHAR(30) NOT NULL,
	account_status VARCHAR(20) NOT NULL,
	created_date DATETIME,
	last_login_date DATETIME,
	PRIMARY KEY (id),
	UNIQUE (username),
	UNIQUE (email)
);

CREATE TABLE assets (
	id INTEGER NOT NULL,
	asset_name VARCHAR(150) NOT NULL,
	asset_type VARCHAR(80) NOT NULL,
	ip_address VARCHAR(45),
	department VARCHAR(100) NOT NULL,
	owner_id INTEGER NOT NULL,
	criticality VARCHAR(20) NOT NULL,
	status VARCHAR(30) NOT NULL,
	created_date DATETIME,
	PRIMARY KEY (id)
);
