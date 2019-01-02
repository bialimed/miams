/**
 *
 * Copyright (C) 2018 IUCT-O
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 * @author  Frederic Escudie
 * @license  GNU General Public License
 * @version  1.2.0
 */

function sortNumber(a,b) {
    return a - b;
}

String.prototype.capitalize = function() {
    return this.replace(/(?:^|\s)\S/g, function(a) { return a.toUpperCase(); });
};


function getMethods(data) {
    let methods = new Set()
    data.forEach(function(curr_spl){
        Object.keys(curr_spl.results).forEach(function(curr_method){
            methods.add(curr_method)
        })
    })
    methods = Array.from(methods)
    methods.sort()
    return methods
}

function selectSample( spl_data, methods, distrib_method, pre_zoom_min=null, pre_zoom_max=null ){
    drawSampleStatus('sample-status', spl_data, methods)
    drawSampleTable('sample-summary-table', spl_data, methods)
    drawSizeGraph('length-graph', spl_data.loci, distrib_method, pre_zoom_min, pre_zoom_max)
    drawLociTable('nb-seq-table', spl_data.loci, methods)
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

function drawSampleStatus( container_id, sample_data, methods ){
    // Get consensus status
    let pred_status = []
    methods.forEach(function (curr_method) {
        pred_status.push(
            sample_data.results[curr_method].status
        )
    })
    pred_status = Array.from(new Set(pred_status))
    status = null
    if( pred_status.length == 1 ){
        status = pred_status[0]
    } else {
        status = "Ambiguous"
    }
    // Display
    $("#" + container_id).html(status)
    $("#" + container_id).removeClass("status-MSI")
    $("#" + container_id).removeClass("status-MSS")
    $("#" + container_id).removeClass("status-Ambiguous")
    $("#" + container_id).removeClass("status-Undetermined")
    $("#" + container_id).addClass("status-" + status)
}


function drawSampleTable( container_id, sample_data, methods ){
    // Prepare data
    let rows_data = new Array()
    methods.forEach(function (curr_method) {
		let score = displayedScore(sample_data.results[curr_method].score)
		if( score !== null ){
			const score_class = (score >= 0.85 ? "score" : "score score-warning")
			score = '<span class="' + score_class + '">' + score + '</span>'
		}
		rows_data.push([
            curr_method,
            score,
            sample_data.results[curr_method].status
        ])
    })
    // Create/Clear datatable
    $("#" + container_id).removeClass("d-none")
    let datatable = null
    if($.fn.dataTable.isDataTable("#" + container_id)){
        datatable = $("#" + container_id).DataTable()
        datatable.clear()
    } else {
        datatable = $("#" + container_id).DataTable({"bPaginate": false, "info": false, "searching": false})
    }
    // Add data
    datatable.rows.add(rows_data)
    // Add class on status cells
    datatable.columns(2).nodes()
        .flatten()
        .to$()
        .each( function (idx, td) {
            td.className = 'sticker status-' + td.textContent
        })
    // Draw
    datatable.draw()
}

function ntile(data, step, nb_shunk=100){
    const sorted_data = data.sort(sortNumber)
    let data_idx = null
    let percentile_value = null
    if( step == 0 ){
        percentile_value = sorted_data[0]
    } else if( step == nb_shunk ){
        percentile_value = sorted_data[data.length - 1]
    } else {
        const data_idx = Math.ceil((step * sorted_data.length)/nb_shunk) - 1
        percentile_value = sorted_data[data_idx]
    }
    return percentile_value
}

function addMethodsInTable(methods){
    methods.forEach(function (curr_method) {
        const header_row = $("#nb-seq-table thead tr")
        header_row.append("<th>" + curr_method + " nb reads</th>")
        header_row.append("<th>" + curr_method + " score</th>")
        header_row.append("<th>" + curr_method + " status</th>")
    })
}

function getLocusIdByName(data_by_spl){
    let locus_id_by_name = {}
    for(let spl_id in data_by_spl){
        const spl = data_by_spl[spl_id]
        for(let locus_id in spl.loci){
            const locus_name = spl.loci[locus_id].name
            locus_id_by_name[locus_name] = locus_id
        }
    }
    return locus_id_by_name
}

function drawSizeGraph( container_id, data, method, pre_zoom_min=null, pre_zoom_max=null ){
    // Transforms data to series
    let series = []
    const loci_ids = Object.keys(data).sort()
    loci_ids.forEach(function (key) {
        const locus = data[key]
        const nb_by_length = locus.results[method].data["nb_by_length"]
        const lengths = Object.keys(nb_by_length).sort(sortNumber)
        // Set series
        let series_data = []
        lengths.forEach(function (key) {
            series_data.push([parseInt(key), nb_by_length[key]])
        })
        series.push({
            "name": locus.name,
            "data": series_data,
            "zIndex": 1
        })
    })
    // Draws graph
    Highcharts.chart(
        container_id,
        {
            chart: {
                type: "column",
                zoomType: "x",
                events: {
                    load: function(){
                        if(pre_zoom_min != null || pre_zoom_max != null){
                            this.xAxis[0].setExtremes(pre_zoom_min, pre_zoom_max)
                            this.showResetZoom()
                        }
                    }
                }
            },
            title: {
                text: 'Fragments lengths'
            },
            plotOptions: {
                series: {
                    events: {
                        afterAnimate: function(evt){
                            const locus_id = locus_id_by_name[evt.target.name]
                            const locus_peaks = models_peaks_by_locus[locus_id]
                            if(locus_peaks.length != 0){
                                this.chart.xAxis[0].addPlotBand({
                                    "from": ntile(locus_peaks, 0),
                                    "to": ntile(locus_peaks, 100),
                                    "color": evt.target.color,
                                    "className": "max-interval",
                                    "id": "models_peak_" + evt.target.name
                                })
                            }
                        },
                        hide: function (evt) {
                            this.chart.xAxis[0].removePlotBand(
                                "models_peak_" + evt.target.name
                            )
                        },
                        show: function (evt) {
                            const locus_id = locus_id_by_name[evt.target.name]
                            const locus_peaks = models_peaks_by_locus[locus_id]
                            if(locus_peaks.length != 0){
                                this.chart.xAxis[0].addPlotBand({
                                    "from": ntile(locus_peaks, 0),
                                    "to": ntile(locus_peaks, 100),
                                    "color": evt.target.color,
                                    "className": "max-interval",
                                    "id": "models_peak_" + evt.target.name
                                })
                            }
                        }
                    }

                }
            },
            xAxis: {
                tickInterval: 1,
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
                crosshairs: [true],
                shared: true,
                formatter: function() {
                    let lines = ['Nb amplicons for <b>' + this.points[0].x + 'nt</b>:']
                    $.each(this.points, function(idx, point) {
                        lines.push(
                            '<b><span style="color:' + point.series.color + '">' + point.series.name + '</b></span>' +
                            ': ' +
                            '<b>' + point.y + '</b>'
                        )
                    });
                    return lines.join('<br />')
                }
            },
            credits: {
                enabled: false
            },
            series: series
        }
    );
}

function getNbReads(method, result){
    let nb_reads = null
    if(result.data.hasOwnProperty("nb_reads")){
        nb_reads = result.data["nb_reads"]
    } else {
        nb_reads = 0
        const lengths = Object.keys(result.data["nb_by_length"])
        lengths.forEach(function (curr_length) {
            nb_reads += result.data["nb_by_length"][curr_length]
        })
        if(result._class == "LocusResPairsCombi"){  // Method based on fragments instead of reads
            nb_reads = nb_reads * 2
        }
    }
    return nb_reads
}

function displayedScore(val, prec=3, fixed=true){
    let displayed = null
    if( val != null ){
        displayed = Number.parseFloat(
            Math.round(val * Math.pow(10, prec))/
            Math.pow(10, prec)
        )
        if(fixed){
            displayed.toFixed(prec)
        }
    }
    return displayed
}

function drawLociTable( container_id, data, methods ){
    // Prepare data
    let status_columns = []
    const loci_ids = Object.keys(data).sort()
    let rows_data = new Array()
    loci_ids.forEach(function (key) {
        const locus = data[key]
			let curr_row = [locus.position, locus.name]
			methods.forEach(function (curr_method) {
			let score = displayedScore(locus.results[curr_method].score)
			if( score !== null ){
				const score_class = (score >= 0.90 ? "score" : "score score-warning")
				score = '<span class="' + score_class + '">' + score + '</span>'
			}
            curr_row = curr_row.concat([
                getNbReads(curr_method, locus.results[curr_method]),
                score,
                locus.results[curr_method].status
            ])
            status_columns.push(curr_row.length - 1)
        })
        rows_data.push(curr_row)
    });
    // Create/Clear datatable
    $("#" + container_id).removeClass("d-none")
    let datatable = $("#" + container_id).DataTable()
    datatable.clear()
    // Add data
    datatable.rows.add(rows_data)
    // Add class on status cells
    status_columns.forEach(function (col_idx) {
        datatable.columns(col_idx).nodes()
            .flatten()
            .to$()
            .each( function (idx, td) {
                td.className = 'sticker status-' + td.textContent
            })
    })
    // Draw
    datatable.draw()
}
