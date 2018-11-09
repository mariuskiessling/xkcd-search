var app = new Vue({
  el: '#app',
  data: {
    query: '',
    results: [],
    loading: false,
    searchPerformed: false
  },
  methods: {
    search: function () {
      this.loading = true;
      axios.get('http://big-data.mariuskiessling.de:5000/search/' + this.query).then(response => {
        this.loading = false;
        this.results = response.data;
        this.searchPerformed = true;
      }).catch(error => {
        console.log(error);
        alert("An error occurred while trying to process your search. Please make sure that the API ist started and is functioning properly.");
        this.loading = false;
        this.searchPerformed = false;
      });
    }
  }
});