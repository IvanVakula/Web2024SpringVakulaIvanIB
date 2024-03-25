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


@app.route('/form2', methods=['GET', 'POST'])
def form2():
    error_message = ''
    phone_number = ''

    if request.method == 'POST':
        phone_number = request.form.get('param1')
        cleaned_number = (phone_number.replace(' ', '').replace('.', '')
                          .replace('(', '').replace(')', '')
                          .replace('-', '').replace('+', '')
        )

        if not cleaned_number.isdigit():
            error_message = 'Недопустимый ввод. В номере телефона встречаются недопустимые символы.'

        elif len(cleaned_number) not in [10, 11]:
            error_message = 'Недопустимый ввод. Неверное количество цифр.'

        elif phone_number.startswith(('8', '+7')) and len(cleaned_number) == 11:
            phone_number = '8-' + cleaned_number[1:4] + '-' + cleaned_number[4:7] + '-' + cleaned_number[7:9] + '-' + cleaned_number[9:]

        elif len(cleaned_number) == 10:
            phone_number = cleaned_number[0:3] + '-' + cleaned_number[3:6] + '-' + cleaned_number[6:8] + '-' + cleaned_number[8:]

    return render_template('form2.html', error_message=error_message, phone_number=phone_number, request=request)


if __name__ == '__main__':
    app.run(debug=True)


