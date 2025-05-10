SET
  SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET
  time_zone = "+00:00";

CREATE TABLE `images` (
  `img_id` int(255) NOT NULL,
  `img_url` varchar(255) NOT NULL
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_general_ci;

ALTER TABLE
  `images`
ADD
  PRIMARY KEY (`img_id`);
  
ALTER TABLE
  `images`
MODIFY
  `img_id` int(255) NOT NULL AUTO_INCREMENT;
COMMIT;