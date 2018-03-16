/*
# Copyright (C) 2018 IUCT-O
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/
function sortNumber(a,b) {
    return a - b;
}

String.prototype.capitalize = function() {
    return this.replace(/(?:^|\s)\S/g, function(a) { return a.toUpperCase(); });
};


function selectSample( spl_data ){
	fillSample('sample-summary', spl_data)
	drawSizeGraph('length-graph', spl_data["loci"]);
	drawTable('nb-seq-table', spl_data["loci"]);
}

function navButtonUpdate(select_spl){
	const curr_idx = select_spl.prop('selectedIndex')
	if(curr_idx == Object.keys(data_by_spl).length - 1){
		$("#next-spl").addClass("disabled")
	} else {
		$("#next-spl").removeClass("disabled")
	}
	if(curr_idx == 0){
		$("#prev-spl").addClass("disabled")
	} else {
		$("#prev-spl").removeClass("disabled")
	}
}

function fillSample( container_id, data ){
	const status = data["sample"]["is_stable"] == null ? "unknown" : (data["sample"]["is_stable"] ? "stable" : "instable")
	$("#" + container_id + " #spl-status").text(status.capitalize())
	$("#" + container_id + " #spl-status").removeClass("status-stable status-unknown status-instable")
	$("#" + container_id + " #spl-status").addClass("status-" + status)
	$("#" + container_id + " #spl-score").text(data["sample"]["score"])
	let loci_metrics = {
		"nb_undefined": 0,
		"nb_instable": 0,
		"nb_stable": 0
	}
	const loci_ids = Object.keys(data["loci"]).sort()
	loci_ids.forEach(function (key) {
		const locus = data["loci"][key]
		if(locus["is_stable"] == null){
			loci_metrics["nb_undefined"] += 1
		} else if(locus["is_stable"]){
			loci_metrics["nb_stable"] += 1
		} else {
			loci_metrics["nb_instable"] += 1
		}
	})
	$("#" + container_id + " #spl-stable-loci").text(
		loci_metrics["nb_stable"] + "/" + loci_ids.length
	)
	$("#" + container_id + " #spl-instable-loci").text(
		loci_metrics["nb_instable"] + "/" + loci_ids.length
	)
	$("#" + container_id + " #spl-unknown-loci").text(
		loci_metrics["nb_undefined"] + "/" + loci_ids.length
	)
}

function drawSizeGraph( container_id, data, x_min=null, x_max=null ){
	// Transforms data to series
	let series = []
	const loci_ids = Object.keys(data).sort()
	loci_ids.forEach(function (key) {
		const locus = data[key]
		const nb_by_lengths = locus["pairs_combination"]["nb_by_lengths"]
		const lengths = Object.keys(nb_by_lengths).sort(sortNumber)
        // Set series
		let series_data = []
		lengths.forEach(function (key) {
			series_data.push([parseInt(key), nb_by_lengths[key]])
		})
		series.push({
			"name": locus["name"],
			"data": series_data
		})
	})
	// Draws graph
	Highcharts.chart(
		container_id,
		{
			chart: {
				type: "column",
				zoomType: "x"
			},
			title: {
				text: 'Fragments lengths'
			},
			xAxis: {
				tickInterval: 1,
				min: x_min,
				max: x_max,
				title: {
					text: "Length"
				}
			},
			yAxis: {
				title: {
					text: "Nb amplicons"
				}
			},
			tooltip: {
				headerFormat: '<b>{series.name}</b><br />',
				pointFormat: '<b>{point.x}nt</b>: <b>{point.y}</b> amplicons'
			},
			credits: {
				enabled: false
			},
			series: series
		},
		/*function(e){ // Redraw chart to prevent problem with scrollbar
			setTimeout(function() {
				const container = $("#" + container_id)
				e.setSize(container.width(), container.height());
			}, 1)
		}*/
	);
}

function drawTable( container_id, data ){
    $("#" + container_id + " tbody tr").remove()
	const loci_ids = Object.keys(data).sort()
	loci_ids.forEach(function (key) {
		const locus = data[key]
		const status = (locus["is_stable"] == null ? "unknown" : (locus["is_stable"] ? "stable" : "instable"))
		const nb_pairs_combined = locus["pairs_combination"]["nb_pairs"]
		$("#" + container_id + " tbody").append(
			"<tr>" +
				"<td>" + locus["position"] + "</td>" +
				"<td>" + locus["name"] + "</td>" +
				'<td class="sticker status-' + status + '">' + status + "</td>" +
				"<td>" + locus["nb_pairs"] + "</td>" +
				"<td>" + (nb_pairs_combined*100/locus["nb_pairs"]).toFixed(2) + "</td>" +
			"</tr>"
		)
	});
	$("#" + container_id).removeClass("d-none");
	$("#" + container_id).DataTable();
}
