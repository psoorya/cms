import os
import io
from flask import Flask, request, render_template, session, flash, redirect, url_for, Response
import mysql.connector
from flask_session import Session
from sdmail import sendmail
from tokenreset import token
from key import secret_key, salt, salt2
from itsdangerous import URLSafeTimedSerializer

app = Flask(__name__)
# Rename secret_key to a different variable name
my_secret_key = secret_key

# Set Flask app configuration for session management
app.config['SESSION_TYPE'] = 'filesystem'

mydb = mysql.connector.connect(user='root', password='admin', host='localhost', database='company')

# Initialize Flask-Session
Session(app)

# ... rest of your code ...

@app.route('/')
def index():
    return render_template('index.html')
@app.route('/user',methods=['GET','POST'])
def user():
    if request.method=='POST':
        first=request.form['first']
        last=request.form['last']
        username=request.form['username']
        emailid=request.form['email']
        phno=request.form['phno']
        password=request.form['password']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*) from user where username=%s',[username])
        count=cursor.fetchone()[0]
        cursor.execute('select count(*) from user where email=%s',[emailid])
        count1=cursor.fetchone()[0]
        cursor.close()
        if count==1:
            flash('username already in use')
            return render_template('register.html')
        elif count1==1:
            flash('Email already in use')
            return render_template('register.html')
        data={'first':first,'last':last,'username':username,'emailid':emailid,'phno':phno,'password':password}
        subject='Email Confirmation'
        body=f"Thanks for signing up\n\nfollow this link for further steps-{url_for('confirm',token=token(data,salt),_external=True)}"
        sendmail(to=emailid,subject=subject,body=body)
        flash('Confirmation link sent to mail')
        return redirect(url_for('userlogin'))
    return render_template('register.html')
@app.route('/confirm/<token>')
def confirm(token):
    try:
        serializer=URLSafeTimedSerializer(secret_key)
        data=serializer.loads(token,salt=salt,max_age=180)
    except Exception as e:
        #print(e)
        return 'Link Expired register again'
    else:
        cursor=mydb.cursor(buffered=True)
        name=data['username']
        cursor.execute('select count(*) from user where username=%s',[name])
        count=cursor.fetchone()[0]
        if count==1:
            cursor.close()
            flash('You are already registerterd!')
            return redirect(url_for('userlogin'))
        else:
            cursor.execute('insert into user(first,last,username,email,phno,password )values(%s,%s,%s,%s,%s,%s)',[data['first'],data['last'],data['username'],data['emailid'],data['phno'],data['password']])
            mydb.commit()
            cursor.close()
            flash('Details registered!')
            return redirect(url_for('userlogin'))
@app.route('/userlogin',methods=['GET','POST'])
def userlogin():
    if request.method=='POST':
        print(request.form)
        email=request.form['email']
        password=request.form['password']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('SELECT count(*) from user where email=%s and password=%s',[email,password])
        count=cursor.fetchone()[0]
        cursor.close()
        if count == 1:
            session['user'] = email
            return redirect(url_for('userpanel'))

        else:
            flash('Invalid username or password')
            return render_template('userlogin.html')
    return render_template('userlogin.html')
@app.route('/userpanel')
def userpanel():
    return render_template('userpanel.html')

@app.route('/myarticle.html')
def my_article():
    return render_template('myarticle.html')

@app.route('/fileupload.html')
def fileupload():
    return render_template('fileupload.html')


def get_article_by_id(article_id):
    for article in articles:
        if article['id'] == article_id:
            return article
    return None


articles = []
@app.route('/add_article', methods=['GET', 'POST'])

def add_article():
    if request.method == 'POST':
        # Get the form data
        title = request.form['title']
        information = request.form['information']
        image = request.form['image']

        if title and information and image:
            # Create a new article with a unique ID
            article = {
                'id': len(articles) + 1,  # Assign a unique ID
                'title': title,
                'information': information,
                'image': image,
            }
            articles.append(article)

    return render_template('addarticle.html')


@app.route('/list_notes')
def list_notes():
    return render_template('myarticle.html', data=articles)


@app.route('/view_article/<int:article_id>')
def view_article(article_id):
    article = get_article_by_id(article_id)
    if article is None:
        return "Article not found", 404

    return render_template('viewarticle.html', article=article)


# Define a sample article dictionary. Replace this with your actual data retrieval logic.
articles = {
    1: {"id": 1, "title": "Sample Article", "content": "This is a sample article."},
    # Add more articles as needed.
}

@app.route('/update_article/<int:article_id>')
def update_article(article_id):
    # Check if the article exists in your data source.
    article = articles.get(article_id)
    if article is None:
        # Handle the case where the article does not exist.
        return "Article not found", 404  # You can customize this response as needed.

    # If the article exists, render the template with the article object.
    return render_template('updatearticle.html', article=article)




@app.route('/delete_note/<int:nid>')
def delete_note(nid):
    article = get_article_by_id(nid)

    if article:
        articles.remove(article)  # Remove the article from the list (you may need to update this logic to match your data source)

        flash('Article deleted successfully.')
    else:
        flash('Article not found.')

    return redirect(url_for('list_notes'))


@app.route('/create_flex_box', methods=['POST'])
def create_flex_box():
    title = request.form['title']
    information = request.form['information']
    image = request.form['image']

    if title and information and image:
        article = {
            'title': title,
            'information': information,
            'image': image,
        }
        articles.append(article)

    return redirect(url_for('list_notes'))


@app.route('/userlogout')
def userlogout():
    if session.get('user'):
        session.pop('user')
        flash('Successfully logged out')
        return redirect(url_for('userlogin'))
    else:
        return redirect(url_for('userlogin'))
@app.route('/forgetpassword',methods=['GET','POST'])
def forget():
    if request.method=='POST':
        email=request.form['id']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select email from user')
        data=cursor.fetchall()
        if (email,) in data:
            cursor.execute('select email from user where email=%s',[email])
            data=cursor.fetchone()[0]
            cursor.close()
            session['pass']=email
            sendmail(data,subject='Reset password',body=f'Reset the password here -{request.host+url_for("createpassword")}')
            flash('reset link sent to your mail')
            return redirect(url_for('userlogin'))
        else:
            return 'Invalid user id'
    return render_template('forgot.html')
@app.route('/createpassword',methods=['GET','POST'])
def createpassword():
    if request.method=='POST':
        oldp=request.form['npassword']
        newp=request.form['cpassword']
        if oldp==newp:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('update user set password=%s where email=%s',[newp,session.get('pass')])
            mydb.commit()
            flash('Password changed successfully')
            return redirect(url_for('userlogin'))
        else:
            flash('New password and confirm passwords should be same')
            return render_template('newpassword.html')
    return render_template('newpassword.html')



app.run()
