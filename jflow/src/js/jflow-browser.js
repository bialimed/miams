

(function (JflowBrowser, $) {
    var self = JflowBrowser;

    var selectedFiles;

    var updateNbFilesSelected = function() {
        var nbFiles = selectedFiles.length;
        $(".fileDialogDialog .ui-dialog-buttonpane .nbFiles").html(nbFiles + " file" + (nbFiles == 1 ? "" : "s") + " selected.");
    }

    self.exec = function(fillFunction, multiple) {
        selectedFiles = [];
        $("#fileDialog").remove(); //Remove old instance
        $("body").append("<div id='fileDialog'>");
        var dom = "#fileDialog";
        $(dom).addClass("modal fade").attr("role", "dialog");
        $(dom).append("<div class='modal-dialog'>")
        $(dom + " .modal-dialog").append("<div class='modal-content'>");
        $(dom + " .modal-content").append("<div class='modal-header'>");
        $(dom + " .modal-header").append('<button type="button" class="close" data-dismiss="modal">&times;</button>');
        $(dom + " .modal-header").append('<h4 class="modal-title">' + (multiple ? "Choose files" : "Choose one file") +
            '</h4>');
        $(dom + " .modal-content").append("<div class='modal-body'>");
        $(dom + " .modal-content").append('<div class="modal-footer"> \
            <button type="button" class="btn btn-default" id="open-server-file" data-dismiss="modal">Open</button> \
            <button type="button" class="btn btn-default" data-dismiss="modal">Cancel</button> \
        </div>');
        $(dom + " .modal-body").append("<div id='filetree'>");
        $(dom + " div#filetree").fileTree({
            script: '/get_user_files',
            multiSelect: true
        }).on('filetreeclicked', function(e, data) {
            var file = data.li.find("a").attr("rel");
            if (data.li.find("input[type=checkbox]").is(":checked")) {
                if (!multiple) {
                    selectedFiles = [];
                    $("div#filetree input[type=checkbox]:checked").prop("checked", false)
                    $("div#filetree li").removeClass("selected")
                    data.li.addClass("selected")
                    data.li.find("input[type=checkbox]").prop("checked", true)
                }
                selectedFiles.push(file)
            }
            else {
                var fileIndex = selectedFiles.indexOf(file);
                if (fileIndex > -1) {
                    selectedFiles.splice(fileIndex, 1);
                }
            }
            updateNbFilesSelected();

        });
        $(dom).modal("show")
        $("#open-server-file").click(function () {
            if (fillFunction) {
                fillFunction(selectedFiles);
            }
        });
        $(".ui-dialog-buttonpane").append("<div class='nbFiles'>");
        $(".nbFiles").html("0 files selected.");
        $(".fileDialogDialog .ui-dialog-buttonpane .nbFiles").off("click").on("click", function() {
            if (selectedFiles.length > 0) {
                $("#filesSelected").remove();
                $("body").append("<div id='filesSelected'>");
                var selectedHtml = "<label class='checkAll'><input class='checkAll' type='checkbox'/> Check all</label>";
                for (var f = 0; f < selectedFiles.length; f++) {
                    var file = selectedFiles[f];
                    selectedHtml += "<label rel='" + file + "' class='labelBlock'><input rel='" + file + "' type='checkbox' class='files'/> " + file + "</label>";
                }
                $("#filesSelected").html(selectedHtml);
                $("#filesSelected").dialog({
                    title: "You selected these files",
                    width: 430,
                    closeText: null,
                    dialogClass: "filesSelectedDialog",
                    buttons: [
                        {
                            text: "Unselect",
                            click: function () {
                                $("#filesSelected input.files[type=checkbox]:checked").each(function() {
                                    var file = $(this).attr("rel");
                                    $("#fileDialog a[rel='" + file + "']").parent("li").removeClass("selected");
                                    $("#fileDialog a[rel='" + file + "']").parent("li").find("input[type=checkbox]").prop("checked", false);
                                    $("#filesSelected label[rel='" + file + "']").remove();
                                    selectedFiles.splice(selectedFiles.indexOf(file), 1);
                                    updateNbFilesSelected();
                                })
                            }
                        }, {
                            text: "Close",
                            click: function () {
                                $(this).dialog("close");
                            }
                        }
                    ]
                });
                $("#filesSelected input.checkAll").off("change").on("change", function() {
                    if ($(this).is(":checked")) {
                        $("#filesSelected input.files[type=checkbox]").prop("checked", true);
                    }
                    else {
                        $("#filesSelected input.files[type=checkbox]").prop("checked", false);
                    }
                })
            }
        })
    }

})(window.JflowBrowser = window.JflowWfformRules || {}, window.jQuery);