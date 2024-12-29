from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Dummy user data for login
users = {'user': 'password'}

# Ensure the data directory exists
if not os.path.exists('data'):
    os.makedirs('data')

@app.route('/')
def home():
    if 'username' in session:
        return render_template('home.html')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username] == password:
            session['username'] = username
            return redirect(url_for('home'))
        flash('Invalid Credentials')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        if username in users:
            flash('Username already exists')
            return redirect(url_for('register'))
        
        users[username] = password
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/scrape', methods=['POST'])
def scrape():
    if 'username' in session:
        search_query = request.form['search_query']
        
        articles = []

        # Scraping PubMed
        pubmed_url = f'https://pubmed.ncbi.nlm.nih.gov/?term={search_query}'
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(pubmed_url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for article in soup.find_all('article', class_='full-docsum'):
            try:
                title = article.find('a', class_='docsum-title').text.strip()
                authors = article.find('span', class_='docsum-authors').text.strip()
                pub_date = article.find('span', class_='docsum-journal-citation').text.strip()
                journal = article.find('span', class_='docsum-journal-citation').text.strip().split('.')[0]
                abstract = article.find('div', class_='full-view-snippet').text.strip()
                articles.append([title, authors, pub_date, journal, abstract])
            except AttributeError:
                continue
        
        # Scraping arXiv
        arxiv_url = f'https://export.arxiv.org/api/query?search_query={search_query}&start=0&max_results=10'
        response = requests.get(arxiv_url, headers=headers)
        soup = BeautifulSoup(response.content, 'xml')
        
        for entry in soup.find_all('entry'):
            try:
                title = entry.find('title').text.strip()
                authors = ', '.join([author.find('name').text.strip() for author in entry.find_all('author')])
                pub_date = entry.find('published').text.strip()
                journal = 'arXiv'
                abstract = entry.find('summary').text.strip()
                articles.append([title, authors, pub_date, journal, abstract])
            except AttributeError:
                continue
        
        df = pd.DataFrame(articles, columns=['Title', 'Authors', 'Publication Date', 'Journal', 'Abstract'])
        csv_path = f'data/{search_query}_articles.csv'
        df.to_csv(csv_path, index=False)
        
        return send_file(csv_path, download_name=f'{search_query}_articles.csv', as_attachment=True)
    
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
