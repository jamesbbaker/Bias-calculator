var margin = {top: 20, right: 20, bottom: 30, left: 50};
var width = 960 - margin.left - margin.right;
var height = 500 - margin.top - margin.bottom;

var num_patients, ctrl_rate, treat_effect;

d3.select("form").on("submit", function() {
  d3.event.preventDefault();
  num_patients = +d3.select("#num_patients").property("value");
  ctrl_rate = +d3.select("#ctrl_rate").property("value");
  treat_effect = +d3.select("#treat_effect").property("value");
  update();
});

var svg = d3.select("#chart").append("svg")
  .attr("width", width + margin.left + margin.right)
  .attr("height", height + margin.top + margin.bottom)
  .append("g")
  .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

var x = d3.scaleLinear()
  .domain([0, 1])
  .range([0, width]);

var y = d3.scaleLinear()
  .range([height, 0]);

var ctrlLine = d3.line()
  .x(function(d) { return x(d.x); })
  .y(function(d) { return y(d.y); });

var treatLine = d3.line()
  .x(function(d) { return x(d.x); })
  .y(function(d) { return y(d.y); });

function update() {
  var ctrlSD = Math.sqrt(ctrl_rate * (1 - ctrl_rate) / num_patients);
  var treatSD = Math.sqrt( (ctrl_rate + treat_effect) * (1 - (ctrl_rate + treat_effect)) / num_patients);
  var ctrlData = [];
  var treatData = [];
  
  for (var i = 0; i <= 1; i += 0.01) {
    ctrlData.push({ x: i, y: d3.randomNormal(ctrl_rate, ctrlSD)(0) });
    treatData.push({ x: i, y: d3.randomNormal(ctrl_rate + treat_effect, treatSD)(0) });
  }
  
  y.domain([0, d3.max([d3.max(ctrlData, function(d) { return d.y; }), d3.max(treatData, function(d) { return d.y; })])]);
  
  svg.selectAll("path.ctrl").remove();
  svg.selectAll("path.treat").remove();
  
  svg.append("path")
    .datum(ctrlData)
    .attr("class", "ctrl")
    .attr("d", ctrlLine);
  
  svg.append("path")
    .datum(treatData)
    .attr("class", "treat")
    .attr("d", treatLine);
}