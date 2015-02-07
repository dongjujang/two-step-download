import os
import requests
import tornado.ioloop
import tornado.web

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.93 Safari/537.36'

class IndexHandler(tornado.web.RequestHandler):
  @tornado.web.asynchronous
  def get(self):
    self.write('running')
    self.finish()

class DownloadHandler(tornado.web.RequestHandler):
  def download(self, session, headers, download_url):
    content_disposition = None    
    response_file = None
    index = 0
    while True:
      try:
        response = session.get(("%s&no=%s" % (download_url, index)), headers=headers, stream=True)
        if not response.ok:
          break
        content_disposition = response.headers.get('content-disposition', '')
        if not '.torrent' in content_disposition:
          index += 1
          continue
        response_file = response.raw.read()
        break
      except Exception as e:
        print e
        break
      
    return content_disposition, response_file
  
  @tornado.web.asynchronous
  def get(self):
    referer = self.get_argument('referer')
    download_url = self.get_argument('download_url')
    status_code = 400
    response_file = None
    content_disposition = None

    for zero in '.':
      if not referer or not download_url:
        status_code = 400
        break

      headers = { 'User-Agent': USER_AGENT, 'referer': referer }
      session = requests.Session()
      try:
        response = session.get(referer, headers=headers)
        if not response.ok:
          status_code = 400
          break
      except Exception as e:
        print e
        status_code = 404
        break

      content_disposition, response_file = self.download(session, headers, download_url)
      if not response_file:
        status_code = 404
        break

      status_code = 200

    self.set_header('Content-Type', 'application/octet-stream')
    self.set_header('Content-Disposition', content_disposition)
    self.set_status(status_code)
    self.write(response_file)
    self.finish()



application = tornado.web.Application([
    (r'/', IndexHandler),
    (r'/download', DownloadHandler),
])

if __name__ == '__main__':
  port = os.environ.get('PORT', 8888)
  application.listen(port)
  tornado.ioloop.IOLoop.instance().start()
