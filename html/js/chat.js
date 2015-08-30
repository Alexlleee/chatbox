(function() {
    var currentUser = null;
    var socketioPort = '8080';
    var url = window.location.hostname + ":" + socketioPort;
    var socket = io.connect(url+'/chat');
    // Grab some references
    var $status = $('#status');
    var $chat_form = $('#chat');
    var $online_users = $("#online-users");
    var $user_info = $('#user-info');
    var $top_users = $("#top-users");
    var $msgTable = $("table.message-list tbody");

    // Bind the chat form
    $chat_form.bind('submit', function() {
        var $input = $(this).find('input');
        socket.emit('chat', $input.val());
        $input.val('');
        return false;
    });

    // List of currently logged-in users
    var users = [];
    var topUsers = [];

    // Bind events to the socket
    socket.on('login_info', function(msg) {
        currentUser = msg;
        $user_info.html('Hello, '+ msg + "!");
    });
    socket.on('messages', function(msg) {
        $.each(msg, function(index,value ) {
            add_msg(value)
        });
        scroll_down();
        message_hover();
    });
    socket.on('top_list', function(msg) {
        topUsers = msg;
        render_top_users();
    });
    socket.on('enter', function(msg) {
        if (users.indexOf(msg) == -1) {
            users.push(msg);
            render_nicks();
        }
    });
    socket.on('exit', function(msg) {
        users = $.grep(users, function(value, index) {
            return value != msg });
        render_nicks();
    });
    socket.on('users', function(msg) {
        users = msg;
        render_nicks();
    });
    socket.on('chat', function(msg) {
        add_msg(msg);
        scroll_down();
        message_hover();
    });
    socket.on('remove_msg', function(messageid) {
        var $row = $('tr[messageid="' + messageid + '"]');
        $row.html("<td>Сообщение удалено</td><td></td>");
    });

    function add_msg(msg){
        var $newMsgElement = get_msg_element(msg);
        $msgTable.append($newMsgElement);
    }

    // Some helper functions
    function render_nicks() {
        var result = $.map(users, function(value, index){
           return '<tr><td>'+ value +'</td></tr>'
        });
        $online_users.html('<tbody>' + result.join('\n') + '</tbody>');
    }

    function render_top_users() {
        var result = $.map(topUsers, function(value, index){
           index += 1;
            return '<tr><td>'+ index + ". " + value +'</td></tr>'
        });
        $top_users.html('<tbody>' + result.join('\n') + '</tbody>');
    }

    function get_msg_element(value){
        var deleteField = '<td></td>';
        if (value[2] == currentUser){
            deleteField = '<td style="vertical-align: middle"><p class="remove"  messageid="' + value[0] +
            '">Удалить</p></td>'
        }
        return $('<tr messageid="' + value[0] + '"><td>' + '[' + value[3] + '] ' + value[2] + ': '
                + value[1] + '</td>'+ deleteField + '</tr>')
    }

    function scroll_down(){
        $("#chat-box-div").scrollTop($("#chat-box-div")[0].scrollHeight);
    }

    function message_hover() {
        $('p.remove').click(function () {
            var messageid = this.getAttribute('messageid');
            socket.emit('remove_msg', messageid);
        });
    }

})();
