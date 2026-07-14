// Инициализация Telegram Web App
const tg = window.Telegram.WebApp;
tg.expand();

// Состояние приложения
let currentUser = null;
let deals = [];
let marketItems = [];
let referrals = [];

// Загрузка данных
document.addEventListener('DOMContentLoaded', function() {
    // Показываем загрузку
    setTimeout(() => {
        document.getElementById('loading').classList.add('hidden');
        loadUserData();
        loadDeals();
        loadMarketItems();
        loadReferrals();
    }, 1000);
});

// Загрузка данных пользователя
function loadUserData() {
    // В реальном приложении здесь будет запрос к боту
    currentUser = {
        id: 123456789,
        username: 'username',
        balance: 1245.50,
        successDeals: 42,
        rating: 4.9,
        referrals: 7
    };
    
    document.getElementById('userBalance').textContent = currentUser.balance.toFixed(2) + ' USD';
    document.getElementById('userName').textContent = '@' + currentUser.username;
    document.getElementById('successDeals').textContent = currentUser.successDeals;
    document.getElementById('rating').textContent = currentUser.rating;
    document.getElementById('referralsCount').textContent = currentUser.referrals;
}

// Загрузка сделок
function loadDeals() {
    const dealsList = document.getElementById('dealsList');
    dealsList.innerHTML = '';
    
    // Пример данных
    const sampleDeals = [
        {
            id: 'GG-2024-001',
            amount: 1250,
            seller: '@john_doe',
            buyer: '@jane_smith',
            status: 'active',
            date: '14.07.2026'
        },
        {
            id: 'GG-2024-002',
            amount: 3750,
            seller: '@alex_tech',
            buyer: '@maria_web',
            status: 'completed',
            date: '12.07.2026'
        },
        {
            id: 'GG-2024-003',
            amount: 500,
            seller: '@crypto_king',
            buyer: '@nft_collector',
            status: 'pending',
            date: '13.07.2026'
        }
    ];
    
    deals = sampleDeals;
    renderDeals(deals);
}

// Рендер сделок
function renderDeals(dealsData) {
    const dealsList = document.getElementById('dealsList');
    dealsList.innerHTML = '';
    
    if (dealsData.length === 0) {
        dealsList.innerHTML = '<p style="text-align: center; color: var(--text-secondary); padding: 40px 0;">У вас пока нет сделок</p>';
        return;
    }
    
    dealsData.forEach(deal => {
        const statusMap = {
            'active': { class: 'status-active', text: '● Активна' },
            'completed': { class: 'status-completed', text: '✅ Завершена' },
            'pending': { class: 'status-pending', text: '⏳ Ожидает' }
        };
        
        const status = statusMap[deal.status] || statusMap.pending;
        
        const dealCard = document.createElement('div');
        dealCard.className = 'deal-card';
        dealCard.setAttribute('data-status', deal.status);
        dealCard.innerHTML = `
            <div class="deal-header">
                <span class="deal-id">#${deal.id}</span>
                <span class="deal-status ${status.class}">${status.text}</span>
            </div>
            <div class="deal-body">
                <div class="deal-amount">
                    <span class="amount-value">${deal.amount.toFixed(0)} USD</span>
                    <span class="amount-label">Сумма сделки</span>
                </div>
                <div class="deal-parties">
                    <div class="party">
                        <span class="party-label">Продавец</span>
                        <span class="party-name">${deal.seller}</span>
                    </div>
                    <div class="party-arrow">→</div>
                    <div class="party">
                        <span class="party-label">Покупатель</span>
                        <span class="party-name">${deal.buyer}</span>
                    </div>
                </div>
            </div>
            <div class="deal-footer">
                <span class="deal-date"><i class="far fa-calendar-alt"></i> ${deal.date}</span>
                <button class="btn-details" onclick="viewDeal('${deal.id}')">Подробнее →</button>
            </div>
        `;
        dealsList.appendChild(dealCard);
    });
}

// Фильтрация сделок
function filterDeals(filter) {
    // Обновляем активную кнопку
    document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    
    if (filter === 'all') {
        renderDeals(deals);
    } else if (filter === 'active') {
        const activeDeals = deals.filter(d => d.status === 'active' || d.status === 'pending');
        renderDeals(activeDeals);
    } else if (filter === 'completed') {
        const completedDeals = deals.filter(d => d.status === 'completed');
        renderDeals(completedDeals);
    }
}

// Переключение вкладок
function switchTab(tabName) {
    // Обновляем кнопки
    document.querySelectorAll('.nav-tab').forEach(tab => tab.classList.remove('active'));
    document.querySelector(`.nav-tab[data-tab="${tabName}"]`).classList.add('active');
    
    // Обновляем контент
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    document.getElementById(`tab-${tabName}`).classList.add('active');
    
    // Отправляем событие в Telegram
    tg.sendData(JSON.stringify({ action: 'switchTab', tab: tabName }));
}

// Загрузка товаров
function loadMarketItems() {
    const marketGrid = document.getElementById('marketGrid');
    marketGrid.innerHTML = '';
    
    const items = [
        { id: 1, name: 'Steam Gift Card $50', price: 45.00, seller: '@steam_shop', rating: 4.8, icon: 'fa-gamepad' },
        { id: 2, name: 'Discord Nitro - 1 месяц', price: 8.50, seller: '@discord_seller', rating: 5.0, icon: 'fa-crown' },
        { id: 3, name: 'BTC 0.001 (P2P)', price: 62.00, seller: '@btc_trader', rating: 4.6, icon: 'fa-coins' },
        { id: 4, name: 'USDT TRC20 - 100 USDT', price: 98.50, seller: '@usdt_merchant', rating: 4.9, icon: 'fa-wallet' }
    ];
    
    marketItems = items;
    
    items.forEach(item => {
        const stars = '★'.repeat(Math.floor(item.rating)) + '☆'.repeat(5 - Math.floor(item.rating));
        
        const itemDiv = document.createElement('div');
        itemDiv.className = 'market-item';
        itemDiv.setAttribute('onclick', `viewItem('${item.id}')`);
        itemDiv.innerHTML = `
            <div class="item-image">
                <i class="fas ${item.icon}" style="font-size: 48px; color: #6C63FF;"></i>
            </div>
            <div class="item-info">
                <h3>${item.name}</h3>
                <p class="item-price">${item.price.toFixed(2)} USD</p>
                <span class="item-seller">${item.seller}</span>
                <div class="item-rating">
                    <span style="color: #FFD700;">${stars}</span>
                    <span>(${item.rating.toFixed(1)})</span>
                </div>
            </div>
        `;
        marketGrid.appendChild(itemDiv);
    });
}

// Загрузка рефералов
function loadReferrals() {
    const referralList = document.getElementById('referralList');
    
    const refs = [
        { name: '@alex_master', date: '10.07.2026', earnings: 25.50 },
        { name: '@crypto_bro', date: '08.07.2026', earnings: 15.00 },
        { name: '@nft_artist', date: '05.07.2026', earnings: 45.75 }
    ];
    
    referrals = refs;
    
    document.getElementById('totalReferrals').textContent = refs.length;
    document.getElementById('activeReferrals').textContent = '3';
    document.getElementById('referralCommission').textContent = '142.25';
    document.getElementById('referralEarnings').textContent = '284.50 USD';
    
    // Очищаем список и добавляем рефералов
    const listContainer = referralList;
    listContainer.innerHTML = '<h3>Ваши рефералы</h3>';
    
    refs.forEach(ref => {
        const refItem = document.createElement('div');
        refItem.className = 'referral-item';
        refItem.innerHTML = `
            <span class="ref-name">${ref.name}</span>
            <span class="ref-date">Присоединился: ${ref.date}</span>
            <span class="ref-earnings">+${ref.earnings.toFixed(2)} USD</span>
        `;
        listContainer.appendChild(refItem);
    });
}

// Действия
function viewDeal(dealId) {
    showModal('Детали сделки', `
        <p><strong>Сделка #${dealId}</strong></p>
        <p>Статус: Активна</p>
        <p>Сумма: 1,250 USD</p>
        <p>Продавец: @john_doe</p>
        <p>Покупатель: @jane_smith</p>
        <button onclick="closeModal()" class="btn-primary-small" style="margin-top: 16px;">Закрыть</button>
    `);
}

function viewItem(itemId) {
    const item = marketItems.find(i => i.id == itemId);
    if (item) {
        showModal('Товар', `
            <h3>${item.name}</h3>
            <p style="font-size: 24px; color: var(--primary); font-weight: 700;">${item.price.toFixed(2)} USD</p>
            <p>Продавец: ${item.seller}</p>
            <p>Рейтинг: ${item.rating.toFixed(1)} ⭐</p>
            <button onclick="closeModal()" class="btn-primary-small" style="margin-top: 16px;">Купить</button>
        `);
    }
}

function createDeal() {
    showModal('Создание сделки', `
        <form onsubmit="submitDeal(event)">
            <div style="margin-bottom: 12px;">
                <label>Сумма (USD)</label>
                <input type="number" id="dealAmount" placeholder="Введите сумму" style="width: 100%; padding: 8px; border: 1px solid var(--border-color); border-radius: var(--radius-sm);">
            </div>
            <div style="margin-bottom: 12px;">
                <label>Валюта</label>
                <select id="dealCurrency" style="width: 100%; padding: 8px; border: 1px solid var(--border-color); border-radius: var(--radius-sm);">
                    <option value="USD">USD</option>
                    <option value="EUR">EUR</option>
                    <option value="BTC">BTC</option>
                    <option value="ETH">ETH</option>
                </select>
            </div>
            <button type="submit" class="btn-primary-small">Создать сделку</button>
            <button type="button" onclick="closeModal()" style="margin-left: 8px; background: transparent; border: 1px solid var(--border-color); padding: 8px 16px; border-radius: var(--radius-sm); cursor: pointer;">Отмена</button>
        </form>
    `);
}

function submitDeal(event) {
    event.preventDefault();
    const amount = document.getElementById('dealAmount').value;
    const currency = document.getElementById('dealCurrency').value;
    
    if (!amount || amount <= 0) {
        alert('Введите корректную сумму');
        return;
    }
    
    tg.sendData(JSON.stringify({
        action: 'createDeal',
        amount: parseFloat(amount),
        currency: currency
    }));
    
    closeModal();
    tg.showAlert('Сделка создана! Ожидайте подтверждения.');
}

function showReplenish() {
    showModal('Пополнение баланса', `
        <form onsubmit="submitReplenish(event)">
            <div style="margin-bottom: 12px;">
                <label>Сумма пополнения (USD)</label>
                <input type="number" id="replenishAmount" placeholder="Введите сумму" style="width: 100%; padding: 8px; border: 1px solid var(--border-color); border-radius: var(--radius-sm);">
            </div>
            <button type="submit" class="btn-primary-small">Пополнить</button>
            <button type="button" onclick="closeModal()" style="margin-left: 8px; background: transparent; border: 1px solid var(--border-color); padding: 8px 16px; border-radius: var(--radius-sm); cursor: pointer;">Отмена</button>
        </form>
    `);
}

function submitReplenish(event) {
    event.preventDefault();
    const amount = document.getElementById('replenishAmount').value;
    
    if (!amount || amount <= 0) {
        alert('Введите корректную сумму');
        return;
    }
    
    tg.sendData(JSON.stringify({
        action: 'replenishBalance',
        amount: parseFloat(amount)
    }));
    
    closeModal();
    tg.showAlert('Запрос на пополнение отправлен!');
}

function copyReferralLink() {
    const linkInput = document.getElementById('referralLink');
    linkInput.select();
    document.execCommand('copy');
    tg.showAlert('Ссылка скопирована!');
}

function showNotifications() {
    showModal('Уведомления', `
        <p>🔔 У вас 3 новых уведомления:</p>
        <ul>
            <li>Сделка #GG-2024-001 ожидает подтверждения</li>
            <li>Новое сообщение в поддержке</li>
            <li>Реферал @alex_master совершил сделку</li>
        </ul>
        <button onclick="closeModal()" class="btn-primary-small" style="margin-top: 16px;">Закрыть</button>
    `);
}

function toggleMenu() {
    showModal('Меню', `
        <ul style="list-style: none; padding: 0;">
            <li style="padding: 12px; border-bottom: 1px solid var(--border-color);">👤 Профиль</li>
            <li style="padding: 12px; border-bottom: 1px solid var(--border-color);">📊 Статистика</li>
            <li style="padding: 12px; border-bottom: 1px solid var(--border-color);">⚙️ Настройки</li>
            <li style="padding: 12px;">🚪 Выйти</li>
        </ul>
    `);
}

function showFilters() {
    showModal('Фильтры', `
        <div>
            <p><strong>Категории:</strong></p>
            <label><input type="checkbox" checked> Игры</label><br>
            <label><input type="checkbox" checked> Криптовалюта</label><br>
            <label><input type="checkbox" checked> Подарочные карты</label><br>
            <label><input type="checkbox"> NFT</label><br>
            <button onclick="closeModal()" class="btn-primary-small" style="margin-top: 16px;">Применить</button>
        </div>
    `);
}

function switchLanguage() {
    tg.showAlert('Язык изменён на English');
}

function showSecurity() {
    showModal('Безопасность', `
        <p>🔐 Настройки безопасности</p>
        <ul>
            <li>Двухфакторная аутентификация: Включена</li>
            <li>Устройства: 2 активных сессии</li>
            <li>Последний вход: 14.07.2026 15:30</li>
        </ul>
        <button onclick="closeModal()" class="btn-primary-small" style="margin-top: 16px;">Закрыть</button>
    `);
}

function showNotificationsSettings() {
    showModal('Уведомления', `
        <div>
            <p><strong>Настройки уведомлений:</strong></p>
            <label><input type="checkbox" checked> Новые сделки</label><br>
            <label><input type="checkbox" checked> Сообщения</label><br>
            <label><input type="checkbox"> Маркетинговые</label><br>
            <button onclick="closeModal()" class="btn-primary-small" style="margin-top: 16px;">Сохранить</button>
        </div>
    `);
}

function support() {
    showModal('Поддержка', `
        <p>🛠 Свяжитесь с нами:</p>
        <p>📧 support@ggsel.com</p>
        <p>💬 @GGSelSupport</p>
        <p>⏳ Время ответа: до 24 часов</p>
        <button onclick="closeModal()" class="btn-primary-small" style="margin-top: 16px;">Закрыть</button>
    `);
}

function showTerms() {
    showModal('Условия использования', `
        <h4>Условия использования GGSel</h4>
        <p style="font-size: 13px; color: var(--text-secondary);">
            1. Все сделки проходят через гаранта<br>
            2. Комиссия составляет 5% от суммы сделки<br>
            3. Спорные ситуации решаются администрацией<br>
            4. Запрещены мошеннические действия<br>
            5. Все права защищены
        </p>
        <button onclick="closeModal()" class="btn-primary-small" style="margin-top: 16px;">Закрыть</button>
    `);
}

function showPrivacy() {
    showModal('Конфиденциальность', `
        <h4>Политика конфиденциальности</h4>
        <p style="font-size: 13px; color: var(--text-secondary);">
            Мы собираем только необходимые данные для работы платформы.<br>
            Ваши данные не передаются третьим лицам.<br>
            Все транзакции защищены шифрованием.<br>
            Подробнее на сайте ggsel.net
        </p>
        <button onclick="closeModal()" class="btn-primary-small" style="margin-top: 16px;">Закрыть</button>
    `);
}

// Модальное окно
function showModal(title, content) {
    const modal = document.getElementById('modal');
    document.getElementById('modalTitle').textContent = title;
    document.getElementById('modalBody').innerHTML = content;
    modal.classList.add('active');
}

function closeModal() {
    document.getElementById('modal').classList.remove('active');
}

// Закрытие модалки по клику вне
document.getElementById('modal').addEventListener('click', function(e) {
    if (e.target === this) {
        closeModal();
    }
});

// Обработка данных от Telegram
tg.onEvent('mainButtonClicked', function() {
    tg.sendData(JSON.stringify({ action: 'mainButtonClicked' }));
});
