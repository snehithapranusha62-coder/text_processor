import mysql.connector

# Connect to MySQL Server
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root"
)

cursor = conn.cursor()

#  Create Database
cursor.execute("CREATE DATABASE IF NOT EXISTS college1")
print("Database created successfully!")

#  Use Database
cursor.execute("USE college1")

# 3 Create Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS student1 (
    id INT PRIMARY KEY,
    name VARCHAR(20),
    age INT,
    grade VARCHAR(10)
)
""")
print("Table created successfully!")

# Insert Data
students = [
    (1, "Snehitha", 19, "A"),
    (2, "Rahul", 20, "B"),
    (3, "Anjali", 18, "A"),
    (4,"asvitha",19,"A"),
    (5,"vishnavi",20,"B")
]

insert_query = "INSERT INTO student1 (id, name, age, grade) VALUES (%s, %s, %s, %s)"

for student1 in students:
    try:
        cursor.execute(insert_query, student1)
    except:
        print(f"Record with ID {student1[0]} already exists")

conn.commit()
print("Data inserted successfully!")

# Fetch Data
cursor.execute("SELECT * FROM student1")
rows = cursor.fetchall()

print("\nStudent Records:")
for row in rows:
    print(row)

# Close connection
cursor.close()
conn.close()
