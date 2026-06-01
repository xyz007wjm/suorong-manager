import sqlite3
import os
import sys
import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

# 处理PyInstaller打包后的路径
if getattr(sys, 'frozen', False):
    # 运行exe时：数据库和模板在实际exe目录
    BASE_DIR = os.path.dirname(sys.executable)
    # PyInstaller解压的临时目录（用于打包在exe内的资源）
    RESOURCE_DIR = getattr(sys, '_MEIPASS', BASE_DIR)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    RESOURCE_DIR = BASE_DIR

app = Flask(__name__,
            template_folder=os.path.join(RESOURCE_DIR, 'templates'))
app.secret_key = 'suorong_secret_key_2026'

DATABASE = os.path.join(BASE_DIR, 'suorong.db')

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            customer TEXT NOT NULL,
            product TEXT,
            quantity REAL DEFAULT 0,
            unit_price REAL DEFAULT 0,
            receivable REAL DEFAULT 0,
            received REAL DEFAULT 0,
            profit_loss REAL DEFAULT 0,
            unpaid REAL DEFAULT 0,
            transporter TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE INDEX IF NOT EXISTS idx_customer ON records(customer)
    ''')
    conn.execute('''
        CREATE INDEX IF NOT EXISTS idx_date ON records(date)
    ''')
    conn.commit()
    conn.close()

def row_to_dict(row):
    """Convert sqlite3.Row to dict"""
    if row is None:
        return None
    return dict(row)

def excel_date_to_str(serial):
    """Convert Excel serial date to string"""
    try:
        base = datetime.datetime(1899, 12, 30)
        d = base + datetime.timedelta(days=int(float(serial)))
        return d.strftime('%Y-%m-%d')
    except (ValueError, TypeError):
        return str(serial)

init_db()

@app.route('/')
def index():
    conn = get_db()

    # 总记录数
    total_records = conn.execute('SELECT COUNT(*) FROM records').fetchone()[0]

    # 总客户数
    total_customers = conn.execute('SELECT COUNT(DISTINCT customer) FROM records').fetchone()[0]

    # 本月应收/已收/未付汇总
    stats = conn.execute('''
        SELECT
            COALESCE(SUM(receivable), 0) as total_receivable,
            COALESCE(SUM(received), 0) as total_received,
            COALESCE(SUM(unpaid), 0) as total_unpaid,
            COALESCE(SUM(profit_loss), 0) as total_profit_loss
        FROM records
    ''').fetchone()

    # 近7天趋势
    trend = conn.execute('''
        SELECT date, SUM(receivable) as amount, SUM(received) as paid
        FROM records
        GROUP BY date
        ORDER BY date DESC
        LIMIT 7
    ''').fetchall()

    # 欠款最多的客户TOP10
    top_debtors = conn.execute('''
        SELECT customer, SUM(unpaid) as total_unpaid
        FROM records
        WHERE unpaid > 0
        GROUP BY customer
        ORDER BY total_unpaid DESC
        LIMIT 10
    ''').fetchall()

    # 运输人工作量排行
    top_transporters = conn.execute('''
        SELECT transporter, COUNT(*) as count, SUM(receivable) as total
        FROM records
        WHERE transporter != '' AND transporter IS NOT NULL
        GROUP BY transporter
        ORDER BY count DESC
        LIMIT 10
    ''').fetchall()

    conn.close()

    return render_template('index.html',
                         total_records=total_records,
                         total_customers=total_customers,
                         stats=stats,
                         trend=[row_to_dict(r) for r in trend],
                         top_debtors=top_debtors,
                         top_transporters=top_transporters)

@app.route('/records')
def records():
    conn = get_db()
    page = request.args.get('page', 1, type=int)
    per_page = 30

    # 筛选条件
    customer_filter = request.args.get('customer', '').strip()
    transporter_filter = request.args.get('transporter', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()
    product_filter = request.args.get('product', '').strip()

    query = 'SELECT * FROM records WHERE 1=1'
    count_query = 'SELECT COUNT(*) FROM records WHERE 1=1'
    params = []

    if customer_filter:
        query += ' AND customer LIKE ?'
        count_query += ' AND customer LIKE ?'
        params.append(f'%{customer_filter}%')
    if transporter_filter:
        query += ' AND transporter LIKE ?'
        count_query += ' AND transporter LIKE ?'
        params.append(f'%{transporter_filter}%')
    if date_from:
        query += ' AND date >= ?'
        count_query += ' AND date >= ?'
        params.append(date_from)
    if date_to:
        query += ' AND date <= ?'
        count_query += ' AND date <= ?'
        params.append(date_to)
    if product_filter:
        query += ' AND product LIKE ?'
        count_query += ' AND product LIKE ?'
        params.append(f'%{product_filter}%')

    total = conn.execute(count_query, params).fetchone()[0]
    total_pages = max(1, (total + per_page - 1) // per_page)

    query += ' ORDER BY date DESC, id DESC LIMIT ? OFFSET ?'
    params.extend([per_page, (page - 1) * per_page])

    records_data = conn.execute(query, params).fetchall()

    # 获取筛选后的汇总（传参时去掉最后两个分页参数）
    summary_params = params[:-2] if len(params) > 2 else []
    summary = conn.execute('''
        SELECT
            COALESCE(SUM(receivable), 0) as total_receivable,
            COALESCE(SUM(received), 0) as total_received,
            COALESCE(SUM(unpaid), 0) as total_unpaid,
            COALESCE(SUM(profit_loss), 0) as total_profit_loss,
            COALESCE(SUM(quantity), 0) as total_quantity
        FROM records WHERE 1=1
    ''' + (' AND customer LIKE ?' if customer_filter else '') +
    (' AND transporter LIKE ?' if transporter_filter else '') +
    (' AND date >= ?' if date_from else '') +
    (' AND date <= ?' if date_to else '') +
    (' AND product LIKE ?' if product_filter else ''),
    summary_params).fetchone()

    conn.close()

    return render_template('records.html',
                         records=records_data,
                         page=page,
                         total_pages=total_pages,
                         total=total,
                         summary=summary,
                         customer_filter=customer_filter,
                         transporter_filter=transporter_filter,
                         date_from=date_from,
                         date_to=date_to,
                         product_filter=product_filter)

@app.route('/add', methods=['GET', 'POST'])
def add():
    conn = get_db()

    if request.method == 'POST':
        date = request.form['date']
        customer = request.form['customer']
        product = request.form['product']
        quantity = float(request.form.get('quantity', 0) or 0)
        unit_price = float(request.form.get('unit_price', 0) or 0)
        receivable = float(request.form.get('receivable', 0) or 0)
        received = float(request.form.get('received', 0) or 0)
        profit_loss = float(request.form.get('profit_loss', 0) or 0)
        unpaid = receivable - received - profit_loss
        transporter = request.form['transporter']

        conn.execute('''
            INSERT INTO records (date, customer, product, quantity, unit_price, receivable, received, profit_loss, unpaid, transporter)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (date, customer, product, quantity, unit_price, receivable, received, profit_loss, unpaid, transporter))
        conn.commit()
        conn.close()

        flash('记录添加成功！', 'success')
        return redirect(url_for('records'))

    # 获取现有客户和运输人列表用于下拉提示
    customers_list = [r['customer'] for r in conn.execute('SELECT DISTINCT customer FROM records ORDER BY customer').fetchall()]
    transporters_list = [r['transporter'] for r in conn.execute('SELECT DISTINCT transporter FROM records WHERE transporter != "" AND transporter IS NOT NULL ORDER BY transporter').fetchall()]
    today_str = datetime.date.today().strftime('%Y-%m-%d')
    conn.close()

    return render_template('add.html', customers=customers_list, transporters=transporters_list, today=today_str)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    conn = get_db()
    record = conn.execute('SELECT * FROM records WHERE id = ?', (id,)).fetchone()

    if request.method == 'POST':
        date = request.form['date']
        customer = request.form['customer']
        product = request.form['product']
        quantity = float(request.form.get('quantity', 0) or 0)
        unit_price = float(request.form.get('unit_price', 0) or 0)
        receivable = float(request.form.get('receivable', 0) or 0)
        received = float(request.form.get('received', 0) or 0)
        profit_loss = float(request.form.get('profit_loss', 0) or 0)
        unpaid = receivable - received - profit_loss
        transporter = request.form['transporter']

        conn.execute('''
            UPDATE records SET date=?, customer=?, product=?, quantity=?, unit_price=?,
            receivable=?, received=?, profit_loss=?, unpaid=?, transporter=?
            WHERE id=?
        ''', (date, customer, product, quantity, unit_price, receivable, received, profit_loss, unpaid, transporter, id))
        conn.commit()
        conn.close()

        flash('记录更新成功！', 'success')
        return redirect(url_for('records'))

    conn.close()
    return render_template('edit.html', record=record)

@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    conn = get_db()
    conn.execute('DELETE FROM records WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('记录已删除！', 'success')
    return redirect(url_for('records'))

@app.route('/import_data', methods=['GET', 'POST'])
def import_data():
    if request.method == 'POST':
        import warnings
        warnings.filterwarnings('ignore')
        import xlrd

        file_path = request.form.get('file_path', '').strip()

        if not file_path:
            flash('请输入Excel文件路径', 'error')
            return render_template('import.html')

        if not os.path.exists(file_path):
            flash(f'文件不存在: {file_path}', 'error')
            return render_template('import.html')

        try:
            wb = xlrd.open_workbook(file_path)
            sh = wb.sheet_by_index(0)  # 默认第一个sheet

            # 尝试找有数据的sheet
            if sh.nrows < 5:
                for i in range(wb.nsheets):
                    s = wb.sheet_by_index(i)
                    if s.nrows > 5:
                        sh = s
                        break

            conn = get_db()
            inserted = 0
            skipped = 0

            for r in range(4, sh.nrows):  # 第4行开始是数据
                date_val = sh.cell(r, 0).value
                customer = str(sh.cell(r, 1).value).strip()
                product = str(sh.cell(r, 2).value).strip()

                if not customer or customer == '' or customer == '合计':
                    skipped += 1
                    continue

                # 转换日期
                try:
                    date_str = excel_date_to_str(date_val)
                except:
                    date_str = str(date_val)

                quantity = float(sh.cell(r, 3).value or 0)
                unit_price = float(sh.cell(r, 4).value or 0)
                receivable = float(sh.cell(r, 5).value or 0)
                received = float(sh.cell(r, 6).value or 0)
                profit_loss = float(sh.cell(r, 7).value or 0)
                unpaid = float(sh.cell(r, 8).value or 0)
                transporter = str(sh.cell(r, 9).value).strip() if sh.cell(r, 9).value else ''

                conn.execute('''
                    INSERT INTO records (date, customer, product, quantity, unit_price, receivable, received, profit_loss, unpaid, transporter)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (date_str, customer, product, quantity, unit_price, receivable, received, profit_loss, unpaid, transporter))
                inserted += 1

            conn.commit()
            conn.close()

            flash(f'导入完成！新增 {inserted} 条记录，跳过 {skipped} 条。', 'success')
        except Exception as e:
            flash(f'导入失败: {str(e)}', 'error')

        return redirect(url_for('records'))

    return render_template('import.html')

@app.route('/customers')
def customers():
    conn = get_db()

    page = request.args.get('page', 1, type=int)
    per_page = 30
    search = request.args.get('search', '').strip()

    if search:
        total = conn.execute("SELECT COUNT(DISTINCT customer) FROM records WHERE customer LIKE ?", (f'%{search}%',)).fetchone()[0]
        total_pages = max(1, (total + per_page - 1) // per_page)
        data = conn.execute('''
            SELECT customer,
                   COUNT(*) as record_count,
                   SUM(receivable) as total_receivable,
                   SUM(received) as total_received,
                   SUM(unpaid) as total_unpaid
            FROM records
            WHERE customer LIKE ?
            GROUP BY customer
            ORDER BY total_unpaid DESC
            LIMIT ? OFFSET ?
        ''', (f'%{search}%', per_page, (page - 1) * per_page)).fetchall()
    else:
        total = conn.execute('SELECT COUNT(DISTINCT customer) FROM records').fetchone()[0]
        total_pages = max(1, (total + per_page - 1) // per_page)
        data = conn.execute('''
            SELECT customer,
                   COUNT(*) as record_count,
                   SUM(receivable) as total_receivable,
                   SUM(received) as total_received,
                   SUM(unpaid) as total_unpaid
            FROM records
            GROUP BY customer
            ORDER BY total_unpaid DESC
            LIMIT ? OFFSET ?
        ''', (per_page, (page - 1) * per_page)).fetchall()

    conn.close()

    return render_template('customers.html',
                         customers=data,
                         page=page,
                         total_pages=total_pages,
                         total=total,
                         search=search)

@app.route('/customer_detail/<name>')
def customer_detail(name):
    conn = get_db()
    records_data = conn.execute('''
        SELECT * FROM records WHERE customer = ? ORDER BY date DESC
    ''', (name,)).fetchall()

    summary = conn.execute('''
        SELECT
            COUNT(*) as count,
            SUM(quantity) as total_quantity,
            SUM(receivable) as total_receivable,
            SUM(received) as total_received,
            SUM(unpaid) as total_unpaid,
            SUM(profit_loss) as total_profit_loss
        FROM records WHERE customer = ?
    ''', (name,)).fetchone()

    conn.close()

    return render_template('customer_detail.html', customer=name, records=records_data, summary=summary)

@app.route('/export')
def export():
    import csv
    import io

    conn = get_db()
    data = conn.execute('''
        SELECT date, customer, product, quantity, unit_price, receivable, received, profit_loss, unpaid, transporter
        FROM records ORDER BY date DESC
    ''').fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['日期', '客户名称', '份量/品名', '数量', '单价', '应收款', '已收款', '损益金额', '未付金额', '三轮车'])

    for row in data:
        writer.writerow([row['date'], row['customer'], row['product'], row['quantity'],
                        row['unit_price'], row['receivable'], row['received'],
                        row['profit_loss'], row['unpaid'], row['transporter']])

    response = app.response_class(
        output.getvalue(),
        mimetype='text/csv; charset=utf-8-sig',
        headers={'Content-Disposition': 'attachment; filename=suorong_export.csv'}
    )
    return response

@app.template_filter('format_number')
def format_number(value):
    if value is None:
        return '0.00'
    try:
        return f'{float(value):.2f}'
    except (ValueError, TypeError):
        return '0.00'

@app.template_filter('to_int')
def to_int(value):
    try:
        return int(value)
    except:
        return 0

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5800)
