INSERT INTO energy_type VALUES
 ('ELECTRIC','电力','kWh',0.1229,0.5703), ('WATER','水','t',0.0857,0.344);
INSERT INTO area VALUES
 (1,'南京某工业园区','PARK',NULL), (2,'一车间','WORKSHOP',1),
 (3,'二车间','WORKSHOP',1), (4,'三车间','WORKSHOP',1), (6,'注塑机线','LINE',2);
INSERT INTO device(id,code,name,area_id,energy_type,unit,base_load,max_value) VALUES
 (1,'EL-1001','注塑机线电表',6,'ELECTRIC','kWh',70,1000),
 (2,'EL-1002','空压机房电表',2,'ELECTRIC','kWh',45,1000),
 (3,'EL-1003','装配线电表',3,'ELECTRIC','kWh',55,1000),
 (4,'EL-1004','空调系统电表',3,'ELECTRIC','kWh',30,1000),
 (5,'EL-1005','照明电表',4,'ELECTRIC','kWh',12,1000),
 (6,'WT-2001','水泵房水表',4,'WATER','t',3.5,100);
