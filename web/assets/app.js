(() => {
  const composer = document.getElementById('composer');
  const promptInput = document.getElementById('prompt');
  const sendButton = document.getElementById('send');
  const results = document.getElementById('results');
  const chips = document.querySelectorAll('.chip');
  const history = [];

  const submitLabel = sendButton.textContent;

  const setSending = (state) => {
    sendButton.disabled = state;
    promptInput.disabled = state;
    sendButton.innerHTML = state ? '<span class="spinner" aria-hidden="true"></span>' : submitLabel;
  };

  const createCard = (role, content) => {
    const card = document.createElement('article');
    card.className = `result-card ${role === 'assistant' ? 'assistant' : 'user'}`;

    const avatar = document.createElement('div');
    avatar.className = 'avatar';
    avatar.textContent = role === 'assistant' ? 'MN' : 'YOU';

    const body = document.createElement('div');
    body.className = 'content';
    const paragraph = document.createElement('p');
    paragraph.textContent = content;
    body.append(paragraph);

    card.append(avatar, body);
    return card;
  };

  const appendMessage = (role, content) => {
    const card = createCard(role, content);
    results.append(card);
    card.scrollIntoView({ behavior: 'smooth', block: 'end' });
  };

  const requestChat = async (message) => {
    setSending(true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, history }),
      });

      if (!response.ok) {
        throw new Error('MidNight AI is taking a quick breather. Try again soon.');
      }

      const data = await response.json();
      const reply = data.reply?.trim();
      if (!reply) {
        throw new Error('No response received.');
      }

      appendMessage('assistant', reply);
      history.push({ role: 'assistant', content: reply });
    } catch (error) {
      console.error(error);
      appendMessage('assistant', `⚠️ ${error.message || 'Unexpected issue occurred.'}`);
    } finally {
      setSending(false);
      promptInput.focus();
    }
  };

  composer.addEventListener('submit', (event) => {
    event.preventDefault();
    const message = promptInput.value.trim();
    if (!message) return;

    appendMessage('user', message);
    history.push({ role: 'user', content: message });
    promptInput.value = '';

    requestChat(message);
  });

  chips.forEach((chip) => {
    chip.addEventListener('click', () => {
      const seed = chip.dataset.prompt || chip.textContent;
      if (!seed) return;
      promptInput.value = seed;
      composer.requestSubmit();
    });
  });
})();
