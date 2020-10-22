function debounce(fn, delay){
    var timeoutID = null
    return function(){
        clearTimeout(timeoutID)
        var args = arguments
        var that = this
        timeoutID = setTimeout(function() {
            fn.apply(that, args)
        }, delay)
    }
}
var app = new Vue({
    el: '#app',
    data: {
        text_for_dlp: '',
        typing: false,
        result: "",
        action: "",
        activeButton: "inspect"
    },
    delimiters: ["[[","]]"],
    watch: {
        text_for_dlp: debounce(function() {
            const path = '/dlp_results'
            const options = {
                method: 'POST',
                headers: {'content-type': 'application/json'},
                data: {
                    "text": this.text_for_dlp,
                    "action": this.activeButton
                },
                url: path
            }

            axios(options)
            .then(response => {
                console.log(response)
                this.result = response.data.result
            })
            .catch(error => {
                console.log(error)
            })
        }, 700),

        activeButton: debounce(function() {
            const path = '/dlp_results'
            const options = {
                method: 'POST',
                headers: {'content-type': 'application/json'},
                data: {
                    "text": this.text_for_dlp,
                    "action": this.activeButton
                },
                url: path
            }

            axios(options)
            .then(response => {
                this.result = response.data.result
            })
            .catch(error => {
                console.log(error)
            })
        }, 700)
    }
})