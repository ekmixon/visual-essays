import axios from 'axios'
import Cookies from 'js-cookie'
//import { toQueryString } from '@/utils/'
const tokenService = axios.create({
    baseURL: `https://www.jstor.org/api/labs-jwt-service/`,
    headers: {
        'Content-type': 'application/json',
        Accept: 'application/json'
    }
})
export function getApiToken(appName = 'ugw') {
    const qargs = toQueryString({
        appName,
        uuid: Cookies.get('UUID'),
        AccessSession: Cookies.get('AccessSession'),
        AccessSessionSignature: Cookies.get('AccessSessionSignature'),
        AccessSessionTimedSignature: Cookies.get('AccessSessionTimedSignature')
    })
    return tokenService.get(`iac-jwt?${qargs}`).then(resp => resp.data.jwt)
}
export function toQueryString(obj, pack, delimiter, raw) {
    const parts = []
    Object.keys(obj).forEach((key) => {
        if (Array.isArray(obj[key])) {
            if (pack) {
                const packed = obj[key].join(delimiter || ',')
                parts.push(`${key}=${raw ? packed : encodeURIComponent(packed)}`)
            } else {
                obj[key].forEach(value => parts.push(`${key}=${raw ? value : encodeURIComponent(value)}`))
            }
        } else {
            parts.push(`${key}=${raw ? obj[key] : encodeURIComponent(obj[key])}`)
        }
    });
    return parts.join('&')
}