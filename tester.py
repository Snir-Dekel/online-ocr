# import mysql.connector
#
# mydb = mysql.connector.connect(
#     host="localhost",
#     user="root",
#     password="my_sql_password",
#     database="login_website",
# )
#
# mycursor = mydb.cursor()
#
# sql = "INSERT INTO website_announcements (message) VALUES (%s)"
# text = "Test",
# mycursor.execute(sql, text)
# mydb.commit()
#
# print(mydb)
#
#