const http = require("node:http");

const port = Number(process.env.PORT || 3000);
const apiKey = process.env.PAYMENTS_API_KEY;

http
  .createServer((req, res) => {
    if (req.url === "/healthz") {
      res.writeHead(200).end("ok");
      return;
    }
    res.writeHead(apiKey ? 200 : 500).end(apiKey ? "orders" : "missing key");
  })
  .listen(port);
