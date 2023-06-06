$(document).ready(function () {
    $('.toggle_button').click(function () {
        $('.closed_todo').toggle();
        var buttonHtml = $('.toggle_button').html();
        if (buttonHtml === '<h1>Geschlossene Todos ▲</h1>') {
            $('.toggle_button').html('<h1>Geschlossene Todos</h1>');
        } else {
            $('.toggle_button').html('<h1>Geschlossene Todos</h1>');
        }
    });
    $('.filter').change(function () {
        var selectedOption = $(this).children("option:selected").val();
        $.ajax({
            type: "POST",
            url: "/filter/" + selectedOption,
            success: function () {
                location.reload();
            }
        });
    });
    $('.update').click(function () {
        let todoId = $(this).closest('li').data('todo-id');
        $.ajax({
            url: '/api/todo/' + todoId,
            method: 'GET',
            success: function (todo) {
                let slider = $('<div class="slider"></div>');
                slider.addClass('slider');

                let close = $('<form class="close-form" action="/" method="GET"><button class="close-button" type="submit">X</button></form>');
                close.addClass('close-form');
                close.find('button').addClass('close-button');

                let form = $('<form class="update-form" action="/update/' + todo.id + '" method="POST">' +
                    '<div><label for="title"><button class="open" id="finish"></button></label><input id="title" name="value" value="' + todo.value + '"></div>' +
                    '<div></div>' +
                    '<div><ul><li><label for="deadline">Start</label><input id="start" name="start" type="date" value="' + todo.start + '" readonly></li><li><label for="deadline">Deadline</label><input id="deadline" name="deadline" type="date" value="' + todo.deadline + '"></li><li><label for="priority">Priorität</label><input id="priority" name="priority" type="number" min="1" max="5" value="' + todo.priority + '"></li></ul></div>' +
                    '<div id="descContainer"><label id="descLabel" for="desc">Notiz</label><textarea id="desc" name="description" value="' + todo.description + '"></textarea></div>' +
                    '<div><button id="save" type="submit">Speichern</button></div>' +
                    '</form>');
                form.addClass('update-form');
                form.find('#title').addClass('title-input');
                form.find('.open').addClass('open-button');
                form.find('#descContainer').addClass('desc-container');
                form.find('#descLabel').addClass('desc-label');
                form.find('#desc').addClass('desc-input');
                form.find('#save').addClass('save-button');
                form.find('li').addClass('form-item');
                form.find('input').addClass('form-input');
                form.find('ul').addClass('form-list');
                form.find('.open').on('click', function () {
                    $.ajax({
                        url: '/todo/finish/' + todoId,
                        method: 'POST',
                        success: function (response) {
                        },
                        error: function (error) {
                            console.log('Fehler beim Abschließen des Todos über die API: ' + error);
                        }
                    });
                });


                slider.append(close);
                slider.append(form);

                $('body').append(slider);

                slider.addClass('active');
            },
            error: function () {
                console.log('Fehler beim Abrufen des Todos von der API: ' + this.error);
            }
        });
    });
});