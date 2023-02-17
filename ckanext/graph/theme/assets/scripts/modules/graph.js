Date.prototype.getMonthName = function (lang) {
  lang = lang && lang in Date.locale ? lang : 'en';
  return Date.locale[lang].month_names[this.getMonth()];
};

Date.prototype.getMonthNameShort = function (lang) {
  lang = lang && lang in Date.locale ? lang : 'en';
  return Date.locale[lang].month_names_short[this.getMonth()];
};

Date.locale = {
  en: {
    month_names: [
      'January',
      'February',
      'March',
      'April',
      'May',
      'June',
      'July',
      'August',
      'September',
      'October',
      'November',
      'December',
    ],
    month_names_short: [
      'Jan',
      'Feb',
      'Mar',
      'Apr',
      'May',
      'Jun',
      'Jul',
      'Aug',
      'Sep',
      'Oct',
      'Nov',
      'Dec',
    ],
  },
};

ckan.module('graph', function (jQuery, _) {
  return {
    initialize: function () {
      var date_interval = this.options.config['_date_interval'];

      var intervals = {
        year: 'getFullYear',
        month: 'getMonthNameShort',
        day: 'getDate',
      };

      $.plot(this.el, [this.options.data], this.options.config);

      this.el.bind('plothover', function (event, pos, item) {
        if (item) {
          var d = new Date(item.datapoint[0]);

          var label = [];

          for (var i in intervals) {
            label.push(d[intervals[i]]());
            // When we get to the max interval (year etc.,)
            // Stop building the label
            if (i == date_interval) {
              break;
            }
          }
          var content =
            '<strong>' +
            label.reverse().join('-') +
            ':</strong> ' +
            item.datapoint[1];
          $('#tooltip')
            .html(content)
            .css({ top: item.pageY - 40, left: item.pageX - 40 })
            .fadeIn(200);
        } else {
          $('#tooltip').hide();
        }
      });

      $("<div id='tooltip'></div>")
        .css({
          position: 'absolute',
          display: 'none',
          border: '1px solid #fdd',
          padding: '2px',
          'background-color': '#fee',
          opacity: 0.8,
        })
        .appendTo('body');
    },
  };
});
