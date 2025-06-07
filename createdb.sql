create table if not exists users(
    user_id integer,
    current_role_id integer,
    name text,
    UNIQUE (user_id)
);


create table if not exists money(
    user_name varchar(40),
    amount float,
    UNIQUE (user_name)
);


create table if not exists debts(
    company_name varchar(40),
    amount float,
    UNIQUE (company_name)
);


create table if not exists products(
    id integer primary key,
    poster_id integer,
    name varchar(80),
    type varchar(80),
    price float,
    category varchar(80),
    unit varchar(3)
);


create table if not exists product_price(
    product_id integer,
    price float
);


create table if not exists messages(
    user_id integer,
    created datetime,
    message text,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);


create table if not exists actions(
    action_id integer primary key,
    user_id integer,
    action_type varchar(40),
    comment varchar(500),
    created datetime,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);


create table if not exists expense(
    id integer primary key,
    amount integer,
    category varchar(40),
    action_id integer,
    FOREIGN KEY(category) REFERENCES categories(category),
    FOREIGN KEY(action_id) REFERENCES action_id(action_id)
);


create table if not exists product_changes(
    product_id integer,
    quantity float,
    action_id integer,
    FOREIGN KEY(product_id) REFERENCES product(id),
    FOREIGN KEY(action_id) REFERENCES action_id(action_id)
);


INSERT INTO money
VALUES
("Счет", 0),
("Касса", 0),
("Мириан", 0),
("Никита", 0);


INSERT INTO users
VALUES
(358058423, 2, "Никита"),
(1268471021, 1, "Мириан"),
(368555562, 2, "Юля"),
(5852542325, 2, "Коля"),
(651083072, 3, "Миша"),
(1605440975, 4, "Серёга"),
(5389969711, 3, "Илья");