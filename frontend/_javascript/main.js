var app = new Vue({
  el: '#app',
  data: {
    query: '',
    results: ''
  },
  methods: {
    search: function() {
      axios
        .get('http://127.0.0.1:5000/search/' + this.query)
        .then(response => (this.results = response.data))
    }
  }
})
