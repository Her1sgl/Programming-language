const DB_NAME = 'my_secure_pwa_db';
const App = {
  data: [],


  init() {
    this.cacheDOM();
    this.bindEvents();
    this.loadData();
    this.render();
  },


  cacheDOM() {
    this.dom = {
      tableBody: document.querySelector('#passwordsTableBody'),
      form: document.querySelector('#addForm'),
      inputs: {
        name: document.querySelector('#siteName'),
        login: document.querySelector('#login'),
        url: document.querySelector('#url'),
        pass: document.querySelector('#password'),
      },
      genBtn: document.querySelector('#btnGenerate'),
      genOptions: {
        len: document.querySelector('#pwdLength'),
        upper: document.querySelector('#useUppercase'),
        nums: document.querySelector('#useNumbers'),
        sym: document.querySelector('#useSymbols'),
      }
    };
  },


  bindEvents() {
    this.dom.form.addEventListener('submit', (e) => this.addItem(e));
    this.dom.genBtn.addEventListener('click', () => this.setGeneratedPassword());
    this.dom.tableBody.addEventListener('click', (e) => this.handleTableActions(e));
  },

 
  loadData() {
    const stored = localStorage.getItem(DB_NAME);
    this.data = stored ? JSON.parse(stored) : [];
  },

 
  saveData() {
    localStorage.setItem(DB_NAME, JSON.stringify(this.data));
  },

  
  addItem(e) {
    e.preventDefault();
    const { name, login, url, pass } = this.dom.inputs;

    if (!login.value || !pass.value) {
      alert('Заполните обязательные поля!');
      return;
    }

    const newEntry = {
      _id: Math.random().toString(36).substr(2, 9), 
      title: name.value || 'Без названия',
      user: login.value,
      link: url.value,
      secret: pass.value,
      isMasked: true
    };

    this.data.push(newEntry);
    this.saveData();
    this.render();
    this.dom.form.reset();
  },


  handleTableActions(e) {
    const btn = e.target.closest('button');
    if (!btn) return;

    const action = btn.dataset.act;
    const id = btn.dataset.key;
    
    if (action === 'remove') {
      this.data = this.data.filter(item => item._id !== id);
      this.saveData();
      this.render();
    } 
    
    if (action === 'mask') {
      const item = this.data.find(i => i._id === id);
      if (item) {
        item.isMasked = !item.isMasked;
        this.saveData();
        this.render();
      }
    }
  },


  generate(len = 12) {
    const opts = this.dom.genOptions;
    let pool = 'abcdefghijklmnopqrstuvwxyz';
    if (opts.upper.checked) pool += 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    if (opts.nums.checked) pool += '0123456789';
    if (opts.sym.checked) pool += '!@#$%^&*()_+';


    if (pool.length === 26) pool += '0123456789'; 

    let res = '';
    for (let i = 0; i < len; i++) {
      res += pool.charAt(Math.floor(Math.random() * pool.length));
    }
    return res;
  },

  setGeneratedPassword() {
    let length = parseInt(this.dom.genOptions.len.value);
    if (length < 4) length = 4;
    if (length > 64) length = 64;
    
    this.dom.inputs.pass.value = this.generate(length);
  },

 
  render() {
    if (this.data.length === 0) {
      this.dom.tableBody.innerHTML = '<tr><td colspan="5" style="text-align:center; color:#888;">Список пуст</td></tr>';
      return;
    }

    this.dom.tableBody.innerHTML = this.data.map(item => `
      <tr>
        <td data-label="Описание">${item.title}</td>
        <td data-label="Логин">${item.user}</td>
        <td data-label="URL">
          ${item.link ? `<a href="${item.link}" target="_blank">Ссылка</a>` : '-'}
        </td>
        <td data-label="Пароль">
          <span style="font-family: monospace; margin-right:10px;">
            ${item.isMasked ? '••••••••' : item.secret}
          </span>
          <button class="btn-secondary btn-inline" data-key="${item._id}" data-act="mask">
            ${item.isMasked ? '👁' : '✖'}
          </button>
        </td>
        <td data-label="Действия">
          <button class="btn-danger" data-key="${item._id}" data-act="remove">Удалить</button>
        </td>
      </tr>
    `).join('');
  }
};


document.addEventListener('DOMContentLoaded', () => {
  App.init();
  setupSW();
});


function setupSW() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('./service-worker.js')
      .then(() => console.log('SW Ready'))
      .catch(err => console.error('SW Fail', err));
  }
}