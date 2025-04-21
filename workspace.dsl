workspace {

    model {
        anonymousUser = person "Anonymous User" "Посетитель, не зарегистрированный в системе"
        registeredUser = person "Registered User" "Пользователь, имеющий аккаунт и доступ к функциональности"

        moderator = person "Moderator" "Модератор, следящий за соблюдением правил"
        admin = person "Administrator" "Администратор системы, управляет пользователями и сервисами"

        emailService = softwareSystem "Email Service" "Сторонняя система отправки email-уведомлений"
        paymentGateway = softwareSystem "Payment Gateway" "Сторонний платёжный шлюз"

        socialNetwork = softwareSystem "Social Network" {
            description "Платформа для общения, публикаций, сообщений, покупок и подписок."

            authService = container "Auth Service" {
                description "Обрабатывает регистрацию, вход, аутентификацию."
                technology "Spring Boot, JWT"
            }

            userService = container "User Service" {
                description "Профили пользователей, настройки, связи между пользователями."
                technology "Spring Boot, PostgreSQL"
            }

            wallService = container "Wall Service" {
                description "Посты, лайки, комментарии, лента новостей."
                technology "Node.js, MongoDB"
            }

            chatService = container "Chat Service" {
                description "Обмен сообщениями между пользователями."
                technology "Go, Redis, WebSockets"
            }

            notificationService = container "Notification Service" {
                description "Генерация уведомлений, отправка email."
                technology "Python, RabbitMQ"
            }

            paymentService = container "Payment Service" {
                description "Покупки, подписки, платный функционал."
                technology "Kotlin, Stripe SDK"
            }

            adminService = container "Admin Service" {
                description "Интерфейс и сервисы для администраторов и модераторов."
                technology "Ruby on Rails"
            }

            apiGateway = container "API Gateway" {
                description "Входная точка системы, маршрутизация."
                technology "Nginx, Kong"
            }

            database = container "User Database" {
                description "Долговременное хранение пользователей"
                technology "PostgreSQL 14"
            }
        }

        anonymousUser -> authService "Регистрируется / входит"
        registeredUser -> apiGateway "Взаимодействует с API"

        apiGateway -> authService "Аутентификация"
        apiGateway -> userService "Работа с профилем"
        apiGateway -> wallService "Посты, лента"
        apiGateway -> chatService "Сообщения"
        chatService -> registeredUser "WebSocket уведомление о новом сообщении"
        chatService -> notificationService "Создаёт уведомление"
        apiGateway -> notificationService "Уведомления"
        apiGateway -> paymentService "Подписка и оплата"
        apiGateway -> adminService "Панель управления (если админ)"

        userService -> database "Читает и записывает данные пользователей"

        notificationService -> emailService "Отправка email-уведомлений"
        paymentService -> paymentGateway "Обработка платежей"

        moderator -> adminService "Модерация контента"
        admin -> adminService "Администрирование системы"
    }

    views {
        systemContext socialNetwork {
            include *
            autolayout lr
            title "System Context: Social Network"
        }

        container socialNetwork {
            include *
            autolayout lr
            title "Container Diagram: Social Network"
        }

        dynamic socialNetwork {
            description "Пользователь отправляет личное сообщение другому пользователю"
            registeredUser -> apiGateway "Запрос на отправку сообщения"
            apiGateway -> chatService "Пересылает сообщение"
            chatService -> registeredUser "WebSocket уведомление о новом сообщении"
            chatService -> notificationService "Создаёт уведомление"
            notificationService -> emailService "Email: Новое сообщение"
        }

        styles {
            element "Person" {
                shape person
                background #08427b
                color #ffffff
            }

            element "SoftwareSystem" {
                background #1168bd
                color #ffffff
            }

            element "Container" {
                background #438dd5
                color #ffffff
            }

            element "Database" {
                shape cylinder
            }
        }
    }
}
