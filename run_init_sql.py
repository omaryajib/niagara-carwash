import psycopg2

# ✅ بيانات الاتصال الخاصة بـ Render (بدلها إذا تغيرات)
DATABASE_URL = "postgresql://niagara_db_user:TXT8S79HEaIzrNTpj6XlaowKE33QacOx@dpg-d09tv60dl3ps7392odcg-a.oregon-postgres.render.com/niagara_db"

# ✅ تحميل محتوى ملف init.sql
with open("init.sql", "r") as file:
    sql_script = file.read()

try:
    # ✅ الاتصال بقاعدة البيانات
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    # ✅ تنفيذ السكريبت
    cursor.execute(sql_script)
    conn.commit()

    print("✅ تم إنشاء الجداول بنجاح.")

except Exception as e:
    print(f"❌ خطأ أثناء التنفيذ: {e}")

finally:
    if conn:
        cursor.close()
        conn.close()
