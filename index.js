const { getLandText } = require("./lib");

const http = require('http');
const express = require('express');
const { urlencoded } = require('body-parser');
const MessagingResponse = require('twilio').twiml.MessagingResponse;

const app = express();
app.use(urlencoded({ extended: false }));

app.post('/sms', async (req, res) => {
  const twiml = new MessagingResponse();
  const message = req.body.Body;
  const landText = await getLandText(message);
 
  twiml.message(landText);
  res.writeHead(200, {'Content-Type': 'text/xml'});
  res.end(twiml.toString());
});

http.createServer(app).listen(4000, () => {
  console.log('Express server listening on port 4000');
});