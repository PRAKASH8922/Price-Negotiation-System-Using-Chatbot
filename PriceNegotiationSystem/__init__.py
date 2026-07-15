import pymysql

# Configure PyMySQL to mimic mysqlclient for Django
pymysql.install_as_MySQLdb()
