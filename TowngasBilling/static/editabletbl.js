"use strict";

$.fn.clicks = function (click_cb, dblclick_cb, timeout) {
    return this.each(function () {
        var click_cnt = 0,
            obj = this;
        $(this).click(function (e) {
            ++click_cnt;
            if (click_cnt == 1)
                setTimeout(function () {
                    if (click_cnt == 1)
                        click_cb(self, e);
                    else
                        dblclick_cb(self, e);

                    click_cnt = 0;
                }, timeout || 300);
        });
    });
};



/* jQuery Plugin */
(function ($) {
    /* Attaching new method to jQuery */
    $.fn.extend({
        /* Plugin's name */
        editabletbl: function (options) {

            /* Iterate through the set of matched elements */
            return this.each(function () {

                var default_options = function () {
                        var options = $.extend({}, {
                            /* CSS Properties for in-place editor */
                            css_properties: ["padding", 
                                             "padding-top", "padding-bottom", "padding-left", "padding-right",
                                             "text-align", 
                                             "font", "font-size", "font-family", "font-weight",
                                             "border", 
                                             "border-top", "border-bottom", "border-left", "border-right"],
                            editor: $("<input>")
                        });
                        options.editor = options.editor.clone();
                        return options;
                    };

                /* Constants */
                const table = $(this);
                const current_options = $.extend(default_options(), options);
                const key = { left: 0x25, up: 0x26, right: 0x27, down: 0x28, enter: 0xd, esc: 0x1b, tab: 0x9, };

                var active_cell,
                    orderingColumn = table.find("th:first-child").addClass("order"),
                    editor = current_options.editor
                                   .css("position", "absolute")
                                   .hide()
                                   .appendTo(table.parent()),
                    columnClick = function (e) {
                        orderingColumn.removeClass("order");
                        orderingColumn = $(e.target);
                        orderingColumn.addClass("order");

                        var idx = orderingColumn.index(),
                            tbody = table.find("tbody"),
                            rows = tbody.children("tr");


                        function comparator(_a, _b) {
                            var a = $(_a).find("td").eq(idx).text(),
                                b = $(_b).find("td").eq(idx).text();

                            if (a < b)
                                return -1;
                            else if (a > b)
                                return 1;
                            return 0;
                        }
                        rows.sort(comparator)
                            .detach()
                            .appendTo(tbody);
                    },
                    showContent = function (e) {
                        var current_row = table.find("td:focus").siblings().first();
                        console.log(current_row.text());
                        console.log($("#table_name").val());
                        console.log(current_row);
                        $("#row-dialog").modal("toggle");
                    },
                    showEditor = function (select) {
                        if (table.hasClass("rw")) {
                            active_cell = table.find("td:focus");
                            if (active_cell.length) {
                                editor.val(active_cell.text())
                                    .removeClass("error")
                                    .show()
                                    .offset(active_cell.offset())
                                    .css(active_cell.css(current_options.css_properties))
                                    .width(active_cell.width())
                                    .height(active_cell.height())
                                    .focus();

                                if (select)
                                    editor.select();
                            }
                        }
                    },
                    setActiveText = function () {
                        var text = editor.val(),
                            event = $.Event("change"),
                            content_backup;

                        if (active_cell.text() === text || editor.hasClass("error"))
                            return true;

                        content_backup = active_cell.html();
                        active_cell.text(text).trigger(event, text);


                        if (event.result === false)
                            active_cell.html(content_backup);
                        else {
                            active_cell.addClass("changed");
                       }

                    },
                    movement = function (elem, keycode) {
                        switch (keycode) {
                            case key.right:
                                return elem.next("td");
                            case key.left:
                                return elem.prev("td");
                            case key.up:
                                return elem.parent().prev().children().eq(elem.index());
                            case key.down:
                                return elem.parent().next().children().eq(elem.index());
                        }
                        return [];
                    };

                editor.blur(function () {
                    setActiveText();
                    editor.hide();
                }).keydown(function (event) {
                    switch (event.which) {
                        case key.enter:
                            setActiveText();
                            active_cell.focus();
                            editor.hide();
                            event.preventDefault();
                            event.stopPropagation();
                            break;
                        case key.esc:
                            editor.val(active_cell.text());
                            active_cell.focus();
                            editor.hide();
                            event.preventDefault();
                            event.stopPropagation();
                            break;
                        case key.tab:
                            active_cell.focus();
                            break;
                        default:
                            if (this.selectionEnd - this.selectionStart === this.value.length) {
                                var move = movement(active_cell, event.which);
                                if (move.length > 0) {
                                    move.focus();
                                    event.preventDefault();
                                    event.stopPropagation();
                                }
                            }
                    }
                })
                .on("input paste", function () {
                    var event = $.Event("validate");
                    active_cell.trigger(event, editor.val());
                    if (event.result === false)
                        editor.addClass("error");
                    else 
                        editor.removeClass("error");
                });

                table.css("cursor", "pointer")
                    .on("click", "thead > tr > th", columnClick)
                    .find("tbody")
                        .clicks(showContent, showEditor)
                        .on("keypress", showEditor)
                        .keydown(function (event) {
                            var prevent = true,
                                move = movement($(event.target), event.which);
                            if (move.length > 0)
                                move.focus();
                            else if (event.which === key.enter) 
                                showEditor(false);
                            else if (event.which === 17 || event.which === 91 || event.which === 93) {
                                showEditor(true);
                                prevent = false;
                            }
                            else
                                prevent = false;
                            
                            if (prevent) {
                                event.stopPropagation();
                                event.preventDefault();
                            }
                        });
                
                table.find("td").prop("tabindex", 1);

                $(window).on("resize", function () {
                    if (editor.is(":visible")) 
                        editor.offset(active_cell.offset())
                            .width(active_cell.width())
                            .height(active_cell.height());
                });
            });
        }
    });
})(jQuery);


$("#addrow_btn").on("click", function () {

    var tr = $("<tr>").addClass("new-row");

    $("#table > thead > tr > th").each(function() {
        $("<td>").attr("tabindex", 1).appendTo(tr);
    });

    $("#table > tbody").append(tr);
});



$("#table").closest("form").submit(function (e) {

    /* Helper Function */
    function colname(table, col) {
        return table.find("th").eq($(col).index()).text();
    }

    /* loop through rows */
    var table = $("#table"),
        new_row_count = 0;

    $("#table > tbody > tr").each(function (i, row) {
        var delta_dict = {};
        $(row).find("td[class=changed]").each(function (j, col) {
            /* delta_dict[column] = value */
            delta_dict[colname(table, col)] = $(col).text();
        });

        if ($.isEmptyObject(delta_dict) === false) {
            var row_id = $(row).find("td:first").text(),
                input_name = $(row).hasClass("new-row") 
                                ? "newrow-" + new_row_count++ 
                                : "id-" + row_id; // Primary Key
            // console.log(input_name);
            /* new row */
            $("<input>").attr({
                name: input_name,
                type: "text",
                class: "hide",
                value: JSON.stringify(delta_dict)
            }).appendTo(table.parent());
        }
    });

    /* Continue form submit */
    return true; 
});
    
$("#table").editabletbl();
