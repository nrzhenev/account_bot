ALTER TABLE products
ADD COLUMN price float;

UPDATE products
SET price =0;