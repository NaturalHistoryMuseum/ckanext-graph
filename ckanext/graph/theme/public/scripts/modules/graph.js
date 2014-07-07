ckan.module('graph', function (jQuery, _) {
  return {

    initialize: function () {

        $.plot(this.el, [this.options.data], this.options.config);

        this.el.bind("plothover", function (event, pos, item) {

            if (item) {
                var content = '<strong>' + item.datapoint[0] + ':</strong> ' + item.datapoint[1];
                $("#tooltip").html(content).css({top: item.pageY-40, left: item.pageX-40}).fadeIn(200);
            } else {
                $("#tooltip").hide();
            }
        });

        $("<div id='tooltip'></div>").css({
			position: "absolute",
			display: "none",
			border: "1px solid #fdd",
			padding: "2px",
			"background-color": "#fee",
			opacity: 0.80
		}).appendTo("body");
    }

  };
});
