// Fetch a histogram and plot it using flot.
function plotHistogram(container, exam, subject, binSize) {
  var url = "/api/histogram_by_subject/" + exam + "/" + subject + "/" + binSize
  $.getJSON(url, function(data) {
    var values = []
    var max = -1
    for(var i = 0; i < data.length; i++) {
      values.push([data[i]._id, data[i].count])
      max = Math.max(max, data[i].count)
    }
    max *= 1.25
    var barWidth = binSize

    container.css("height", "300px")
    $.plot(container, [values], {
      bars: {
        show: true,
        barWidth: barWidth
      },
      xaxis: {
        min: 0,
        max: 10
      },
      yaxis: {
        min: 0,
        max: max
      }
    });

  });
}  


$(function(){
  $(".histogram").each(function() {
    var canvas = $(this).find(".canvas")
    var binSize = 0.5
    var select = $(this).find("select")
    select.change(function() {
      plotHistogram($(canvas), $(this).val(), "*", binSize)
    })
    select.change()
  })
})
