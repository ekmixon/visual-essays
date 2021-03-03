import { mapGetters, mapActions } from 'vuex';
import { getApiToken } from '../api/token'
import { isTokenExpired } from '../api/JWTUtils'

export default {
    computed: { ...mapGetters(['apiToken']) },
    methods: { ...mapActions(['setApiToken']),
        getApiToken() {
            const self = this
            return isTokenExpired(this.apiToken)
                ? getApiToken()
                    .then((token) => {
                        this.setApiToken(token)
                        return token
                    })
                : Promise.resolve(self.apiToken)
        }
    }
}
