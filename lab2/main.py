from flask import Flask, render_template, request, make_response

app = Flask(__name__)
application = app


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/args')
def args():
    return render_template('args.html', request=request)


@app.route('/headers')
def headers():
    return render_template('headers.html', request=request)


@app.route('/cookies')
def cookies():
    resp = make_response(render_template('cookies.html', request=request))
    if 'test_cookie' in request.cookies:
        resp.delete_cookie('test_cookie')
    else:
        resp.set_cookie('test_cookie', 'vakula')
    return resp



@app.route('/form', methods=['GET', 'POST'])
def form():
    return render_template('form.html', request=request)


def do_calc(operand1, operand2, action):
    if not operand1 or not operand2 or not action:
        return ''
    res = 0
    match action:
        case '+':
            res = int(operand1) + int(operand2)
        case '-':
            res = int(operand1) - int(operand2)
        case '*':
            res = int(operand1) * int(operand2)
        case '/':
            res = int(operand1) / int(operand2)
    return res


@app.route('/calc')
def calc():
    operand1 = request.args.get('operand1')
    operand2 = request.args.get('operand2')
    action = request.args.get('action')

    result = do_calc(operand1, operand2, action)

    return render_template('calc.html', result=result)


def is_valid_phone_number(phone):
    for char in phone:
        if char not in '0123456789 ()-+.':
            return False, "Недопустимый ввод. В номере телефона встречаются недопустимые символы."

    digits = ''.join(filter(str.isdigit, phone))
    if phone.startswith('+7') or phone.startswith('8'):
        if len(digits) != 11:
            return False, "Недопустимый ввод. Неверное количество цифр."
    else:
        if len(digits) != 10:
            return False, "Недопустимый ввод. Неверное количество цифр."

    return True, None


def format_phone_number(phone):
    digits = ''.join(filter(str.isdigit, phone))

    if digits.startswith('+7'):
        digits = digits[2:]
    elif digits.startswith(('7', '8')):
        digits = digits[1:]

    return f'8-{digits[:3]}-{digits[3:6]}-{digits[6:8]}-{digits[8:]}'
@app.route('/form2', methods=['GET', 'POST'])
def form2():
    if request.method == 'GET':
        return render_template('form2.html')
    phone_number = request.form['param1']
    is_valid, error_message = is_valid_phone_number(phone_number)
    if is_valid:
        formatted_phone = format_phone_number(phone_number)
        print(formatted_phone)
        return render_template('form2.html', phone_number=phone_number, formatted_phone=formatted_phone)
    else:
        return render_template('form2.html', phone_number=phone_number, error_message=error_message)




if __name__ == '__main__':
    app.run(debug=True)