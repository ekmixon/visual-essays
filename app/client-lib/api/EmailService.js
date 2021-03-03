import axios from 'axios';
export const baseURL = process.env.dataUrl + '/email/';
const EmailService = axios.create({
  baseURL,
  headers: {
    'Content-type': 'text/plain',
    Accept: 'application/ld+json',
  },
});

function getBodyText(options) {
  let body;
  body = options.message + "\n\r" + '[Sent by: ' + options.name
  if (options.role !== '') {
    body = body + ", " + options.role
  }
  if (options.university !== '') {
    body = body + " at " + options.university
  }
  body = body + ']'
  return body
}

export function sendEmail(options, token,receiver) {
  console.log('options in the email service ', options)

  const args = {
    fromAddress: options.email,
    toAddress: receiver,
    messageSubject: 'Plant Humanities Lab Contact us form',
    messageBodyText: getBodyText(options),
  };

  return EmailService
      .post("https://www.jstor.org/api/labs-email-service/", args, { headers: { Authorization: `JWT ${token}` } })

}
