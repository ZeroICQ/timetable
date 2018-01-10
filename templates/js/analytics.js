<script>
$(document).ready(function () {

    var updateFields = function(e, ui) {

        $td = ui.item.closest('td');

        var data = {};

        data[$td.data('x-field')] = $td.data('x-val');
        data[$td.data('y-field')] = $td.data('y-val');
        data.pk = ui.item.data('pk');
        console.log(data);

        $.ajax({
            url: "{{ url_for('update', table=selected_table) }}",
            method: "POST",
            traditional: true,
            data: data,
            error: function() {
                ui.sender.sortable("cancel");
            },
            success : function(data) {

            },
        });

    };

    $( ".sortable" ).sortable({
        connectWith: '.cell',
        revert: true,
        placeholder: "ui-state-highlight",
        forcePlaceholderSize: true,
        tolerance: "pointer",
        receive: updateFields,
        items: 'div.card'
    });

    $('#show_titles').change(function() {
        $('.title').slideToggle();
    });

    $('[name="show_fields"]').change(function() {
        var fieldName = $(this).attr('value');
        $('[data-field-name="'+fieldName+'"]').slideToggle();
    });

    $('button[data-href]').on("click", function() {
        window.open($(this).data('href'));
    });

    $('.collapse-btn').click(function() {
        $(this).parent().siblings('.cell').first().slideToggle('toggle');
        var status = $(this).data('status');
        if (status === 'expand') {
            $(this).data('status', 'collapse');
            $(this).find('i').removeClass('fa-compress');
            $(this).find('i').addClass('fa-expand');
            $(this).find('span').text('Развернуть');
        } else {
            $(this).data('status', 'expand');
            $(this).find('i').removeClass('fa-expand');
            $(this).find('i').addClass('fa-compress');
            $(this).find('span').text('Свернуть');
        }
    });

});
</script
