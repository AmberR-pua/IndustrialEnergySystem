PRAGMA foreign_keys = ON;
CREATE TABLE energy_type (
 code TEXT PRIMARY KEY CHECK(code IN ('ELECTRIC','WATER')),
 name TEXT NOT NULL, unit TEXT NOT NULL,
 standard_coal_factor REAL NOT NULL CHECK(standard_coal_factor>=0),
 carbon_factor REAL NOT NULL CHECK(carbon_factor>=0)
);
CREATE TABLE area (
 id INTEGER PRIMARY KEY, name TEXT NOT NULL,
 area_type TEXT NOT NULL CHECK(area_type IN ('PARK','WORKSHOP','LINE')),
 parent_id INTEGER REFERENCES area(id), CHECK(id != parent_id)
);
CREATE TABLE device (
 id INTEGER PRIMARY KEY, code TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
 area_id INTEGER NOT NULL REFERENCES area(id),
 energy_type TEXT NOT NULL REFERENCES energy_type(code), unit TEXT NOT NULL,
 base_load REAL NOT NULL CHECK(base_load>=0), max_value REAL NOT NULL CHECK(max_value>0),
 enabled INTEGER NOT NULL DEFAULT 1 CHECK(enabled IN (0,1))
);
CREATE TABLE raw_data (
 id INTEGER PRIMARY KEY, device_id INTEGER NOT NULL REFERENCES device(id),
 data_time TEXT NOT NULL CHECK(length(data_time)=19 AND substr(data_time,15,5)='00:00'),
 value REAL NOT NULL CHECK(value>=0), unit TEXT NOT NULL,
 data_quality INTEGER NOT NULL CHECK(data_quality IN (1,2,3)),
 source TEXT NOT NULL CHECK(source IN ('METER','MANUAL')),
 UNIQUE(device_id,data_time)
);
CREATE INDEX idx_raw_time ON raw_data(data_time);
CREATE INDEX idx_raw_quality ON raw_data(data_quality,device_id,data_time);
CREATE TABLE summary (
 id INTEGER PRIMARY KEY, area_id INTEGER NOT NULL REFERENCES area(id),
 energy_type TEXT NOT NULL REFERENCES energy_type(code),
 period_type TEXT NOT NULL CHECK(period_type IN ('HOUR','DAY','MONTH')),
 period_date TEXT NOT NULL, total_value REAL NOT NULL CHECK(total_value>=0),
 standard_coal REAL NOT NULL CHECK(standard_coal>=0),
 carbon_emission REAL NOT NULL CHECK(carbon_emission>=0),
 expected_count INTEGER NOT NULL DEFAULT 0, actual_count INTEGER NOT NULL DEFAULT 0,
 updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 UNIQUE(area_id,energy_type,period_type,period_date)
);
CREATE TABLE alert (
 id INTEGER PRIMARY KEY, device_id INTEGER NOT NULL REFERENCES device(id),
 data_time TEXT NOT NULL, anomaly_type TEXT NOT NULL,
 anomaly_score REAL, level TEXT NOT NULL CHECK(level IN ('LOW','MEDIUM','HIGH')),
 message TEXT NOT NULL, model_version TEXT NOT NULL,
 UNIQUE(device_id,data_time,anomaly_type,model_version)
);
CREATE TABLE forecast_result (
 id INTEGER PRIMARY KEY, device_id INTEGER NOT NULL REFERENCES device(id),
 energy_type TEXT NOT NULL REFERENCES energy_type(code),
 granularity TEXT NOT NULL CHECK(granularity IN ('HOUR','DAY')),
 forecast_time TEXT NOT NULL, value REAL NOT NULL, lower_value REAL, upper_value REAL,
 model_version TEXT NOT NULL, generated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 CHECK(lower_value IS NULL OR lower_value <= value), CHECK(upper_value IS NULL OR value <= upper_value),
 UNIQUE(device_id,granularity,forecast_time,model_version,generated_at)
);
CREATE TABLE collection_log (
 id INTEGER PRIMARY KEY, inserted_count INTEGER NOT NULL,
 start_time TEXT, end_time TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 mode TEXT NOT NULL CHECK(mode IN ('BOOTSTRAP','REPLAY'))
);
