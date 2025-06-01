\-- 題庫資料表擴充
ALTER TABLE questions ADD COLUMN passage TEXT;
ALTER TABLE questions ADD COLUMN analysis TEXT;
ALTER TABLE questions ADD COLUMN difficulty TEXT;
ALTER TABLE questions ADD COLUMN tags TEXT;
