import os
import requests

from argparse import ArgumentParser
from urllib.parse import urlencode
from bs4 import BeautifulSoup


BASE_URL = 'https://drive.google.com/uc?export=download'


def get_confirm_token(response):
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value
    return None


def download_chunks(file_id, destination, chunk_size=2**20, resume=True):
    session = requests.Session()

    start_byte = 0
    if os.path.exists(destination) and resume == True:
        start_byte = os.path.getsize(destination)
        resume_header = {'Range': f'bytes={start_byte}-'}
        print(f'Download will continue at byte: {start_byte}')
    else:
        resume_header = None

    response = session.get(BASE_URL, params={'id': file_id}, headers=resume_header, stream=True)
    token = get_confirm_token(response)

    if token:
        params = {'id': file_id, 'confirm': token}
        response = session.get(BASE_URL, params=params, headers=resume_header, stream=True)

    confirmation_page_pattern = 'action="https://drive.usercontent.google.com/download"'
    if confirmation_page_pattern in response.text:
        soup = BeautifulSoup(response.text, 'html.parser')
        form = soup.find('form', {'id': 'download-form'})
        if form:
            form_data = {input_tag.get('name'): input_tag.get('value') for input_tag in form.find_all('input')}
            form_params = urlencode(form_data)
            download_url = form['action'] + '?' + form_params
            response = session.get(download_url, headers=resume_header, stream=True)

    
    mode = 'ab' if start_byte > 0 else 'wb'
    with open(destination, mode) as f:
        for chunk in response.iter_content(chunk_size):
            if chunk:
                f.write(chunk)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--file-id', required=True)
    parser.add_argument('--destination', '-d', default='./download')
    parser.add_argument('--chunk-size', type=int, default=2**20)
    parser.add_argument('--resume', action='store_true')

    args = parser.parse_args()

    download_chunks(args.file_id, args.destination, chunk_size=args.chunk_size, resume=args.resume)