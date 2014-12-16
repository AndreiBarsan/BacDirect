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

function renderVenn() {
  "use strict"
  // define sets and set set intersections
  $.getJSON("/api/branches", function(data) {
    var sets = []
    for(var i = 0; i < data.length; ++i) {
      sets.push({
        label: data[i].branch,
        size: data[i].count
      })
    }
    var overlaps = []
    for(var i = 0; i < data.length; ++i) {
      for(var j = 0; j < data.length; ++j) {
        overlaps.push({sets: [i, j], size: 0})
      }
    }

    sets = venn.venn(sets, overlaps);
    venn.drawD3Diagram(d3.select("#venn"), sets, 1000, 1000);
  })
  
}


$(function(){
  $('#mainTabs a').click(function(e) {
    e.preventDefault()
    $(this).tab('show')
  })

  renderVenn()

  var binSize = 0.5

  function refreshHistogram(histogram) {
    var select = histogram.find("select")
    var canvas = histogram.find(".canvas")
    var exam = $(select).val()
    
    plotHistogram($(canvas), exam, "*", binSize)
  }

  function refreshAll() {
    $(".histogram").each(function() {
      refreshHistogram($(this))
    })
  }

  $("#binSize").change(function() {
    binSize = parseFloat($(this).val())
    $("#binSizeDisplay").html(binSize)
    refreshAll()
  })
  $("#binSize").val(binSize)
  $("#binSize").change()

  $("#refresh").click(refreshAll)

  $(".histogram").each(function() {
    var select = $(this).find('select')
    var histogram = $(this)
    select.change(function() {
      refreshHistogram(histogram)
    })
    select.change()
  })
})
