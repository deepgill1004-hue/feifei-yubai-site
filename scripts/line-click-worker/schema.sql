-- 蘇菲餘白：LINE 按鈕點擊計數（一天 × 一頁 × 一個位置一列）
CREATE TABLE IF NOT EXISTS clicks (
  day  TEXT    NOT NULL,            -- 台灣日期 YYYY-MM-DD
  page TEXT    NOT NULL,            -- 網址路徑，例：/letters/142-radiofrequency-ultrasound-lift-collagen-20261123.html
  pos  TEXT    NOT NULL,            -- end、answer、video、sidebar、fab、header、footer、page
  n    INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (day, page, pos)
);
