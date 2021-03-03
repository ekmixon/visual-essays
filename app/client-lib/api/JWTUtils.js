require('./base64');

function urlBase64Decode(str) {
    let output = str.replace(/-/g, '+').replace(/_/g, '/');
    switch (output.length % 4) {
        case 0: { break; }
        case 2: { output += '=='; break; }
        case 3: { output += '='; break; }
        default: {
            throw new Error('Illegal base64url string!');
        }
    }
    return decodeURIComponent(atob(output));
}

export function decodeToken(token) {
    if (typeof token === 'string') {
        const parts = token.split('.');
        if (parts.length !== 3) {
            throw new Error('JWT must have 3 parts');
        }
        const decoded = urlBase64Decode(parts[1]);
        if (!decoded) {
            throw new Error('Cannot decode the token');
        }
        return JSON.parse(decoded);
    }
    return token;
}

export function getTokenExpirationDate(token) {
    console.log(token);
    const decoded = decodeToken(token);
    if (!decoded || typeof decoded.exp === 'undefined') {
        return null;
    }
    const date = new Date(0); // The 0 here is the key, which sets the date to the epoch
    date.setUTCSeconds(decoded.exp);
    return date;
}

export function isTokenExpired(token, offsetSeconds) {
    console.log('TOKEN    ', token);
    if (token === null) {
        return true;
    }
    const date = getTokenExpirationDate(token);
    // eslint-disable-next-line
    offsetSeconds = offsetSeconds || 0;
    if (date === null) {
        return true;
    }
    // Token expired?
    return !(date.valueOf() > (new Date().valueOf() + (offsetSeconds * 1000)));
}
