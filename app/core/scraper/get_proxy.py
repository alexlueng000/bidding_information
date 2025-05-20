import requests


def get_proxy():


    url = 'http://www.zdopen.com/ShortProxy/GetIP/?api=202505201551347337&akey=b762c279131d816e&timespan=0&type=1'

    response = requests.get(url)
    proxy_ip = response.json()

    return proxy_ip


if __name__ == '__main__':
    print(get_proxy())
