/**
 * DealFlow360 — Interactive Razorpay Payment Gateway Modal
 * Replicates the complete 3-step Razorpay checkout flow:
 * Step 1: Payment Options (Cards, Netbanking, Wallet, UPI)
 * Step 2: Razorpay Software Private Ltd Bank Mock Page (Success / Failure)
 * Step 3: Processing payment spinner & Signature Verification
 */
(function (global) {
  'use strict';

  const RazorpayGatewayModal = {
    /**
     * Launch the complete Razorpay Checkout Flow.
     * @param {Object} options
     * @param {string} options.order_id
     * @param {number} options.amount (Amount in dollars or rupees)
     * @param {string} options.currency
     * @param {string} options.invoice_number
     * @param {number} options.invoice_id
     * @param {number} options.customer_id
     * @param {Function} options.onSuccess
     * @param {Function} options.onError
     */
    open(options) {
      const {
        order_id = `order_${Date.now()}`,
        amount = 0,
        currency = 'USD',
        invoice_number = 'INV-1001',
        invoice_id,
        customer_id,
        onSuccess,
        onError
      } = options;

      const overlay = document.getElementById('dealflow-modal-overlay');
      if (!overlay) return;

      const displayAmount = Number(amount).toFixed(2);
      const inrAmount = Math.round(amount * 83); // Approx INR conversion for display display

      // Screen 1: Payment Options Modal
      const renderScreen1 = () => {
        overlay.innerHTML = `
          <div class="modal-card razorpay-checkout-modal" style="max-width: 820px; width: 92%; padding: 0; overflow: hidden; border-radius: 12px; box-shadow: 0 20px 40px rgba(0,0,0,0.3); font-family: 'Inter', sans-serif;">
            <div style="display: flex; min-height: 480px;">
              <!-- Left Sidebar Banner -->
              <div style="width: 38%; background: linear-gradient(135deg, #4A3B52 0%, #2A1F33 100%); color: #FFFFFF; padding: 24px; display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                  <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 24px;">
                    <div style="width: 36px; height: 36px; background: rgba(255,255,255,0.2); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 1.1rem;">DF</div>
                    <div>
                      <div style="font-weight: 700; font-size: 1rem; letter-spacing: 0.5px;">DealFlow360</div>
                      <div style="font-size: 0.7rem; opacity: 0.8;">B2B Commercial Operations</div>
                    </div>
                  </div>

                  <div style="background: rgba(255,255,255,0.1); border-radius: 10px; padding: 16px; margin-bottom: 16px; backdrop-filter: blur(4px);">
                    <div style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; opacity: 0.8;">Price Summary</div>
                    <div style="font-size: 1.8rem; font-weight: 800; margin-top: 4px;">$${displayAmount}</div>
                    <div style="font-size: 0.75rem; opacity: 0.85; margin-top: 2px;">(Approx. &#8377;${inrAmount.toLocaleString()}) &bull; Invoice ${invoice_number}</div>
                  </div>

                  <div style="font-size: 0.75rem; background: rgba(255,255,255,0.08); padding: 10px 12px; border-radius: 8px; display: flex; align-items: center; gap: 8px;">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                    <span>Using as <strong>+91 93458 11585</strong></span>
                  </div>
                </div>

                <div style="display: flex; align-items: center; gap: 6px; font-size: 0.7rem; opacity: 0.7;">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                  <span>Secured by <strong>Razorpay</strong></span>
                </div>
              </div>

              <!-- Right Payment Method Selection -->
              <div style="width: 62%; background: #FFFFFF; padding: 24px; display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 1px solid #E2E8F0; padding-bottom: 12px;">
                    <h3 style="margin: 0; font-size: 1rem; color: #0F172A; font-weight: 700;">Payment Options</h3>
                    <button id="rzp-close-btn" style="background: none; border: none; font-size: 1.4rem; color: #64748B; cursor: pointer;">&times;</button>
                  </div>

                  <!-- Tabs Header -->
                  <div style="display: flex; gap: 8px; margin-bottom: 20px; border-bottom: 1px solid #F1F5F9;">
                    <button class="rzp-tab-btn active" data-tab="netbanking" style="padding: 8px 16px; border: none; background: none; font-weight: 600; font-size: 0.85rem; color: #0D9488; border-bottom: 2px solid #0D9488; cursor: pointer;">Netbanking</button>
                    <button class="rzp-tab-btn" data-tab="cards" style="padding: 8px 16px; border: none; background: none; font-weight: 600; font-size: 0.85rem; color: #64748B; cursor: pointer;">Cards</button>
                    <button class="rzp-tab-btn" data-tab="wallet" style="padding: 8px 16px; border: none; background: none; font-weight: 600; font-size: 0.85rem; color: #64748B; cursor: pointer;">UPI / Wallet</button>
                  </div>

                  <!-- Tab Content: Netbanking -->
                  <div id="rzp-tab-netbanking" class="rzp-tab-content">
                    <div style="font-size: 0.75rem; font-weight: 600; color: #475569; margin-bottom: 12px;">Select Popular Bank:</div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 16px;">
                      <button class="rzp-bank-select-btn" data-bank="Razorpay Software Private Ltd Bank" style="padding: 10px; border: 1px solid #CBD5E1; border-radius: 8px; background: #F8FAFC; text-align: left; cursor: pointer; font-weight: 600; font-size: 0.8rem; display: flex; align-items: center; gap: 8px;">
                        <span style="width: 10px; height: 10px; background: #0D9488; border-radius: 50%;"></span>
                        Razorpay Test Bank
                      </button>
                      <button class="rzp-bank-select-btn" data-bank="HDFC Bank" style="padding: 10px; border: 1px solid #CBD5E1; border-radius: 8px; background: #F8FAFC; text-align: left; cursor: pointer; font-weight: 600; font-size: 0.8rem; display: flex; align-items: center; gap: 8px;">
                        <span style="width: 10px; height: 10px; background: #0284C7; border-radius: 50%;"></span>
                        HDFC Bank
                      </button>
                      <button class="rzp-bank-select-btn" data-bank="ICICI Bank" style="padding: 10px; border: 1px solid #CBD5E1; border-radius: 8px; background: #F8FAFC; text-align: left; cursor: pointer; font-weight: 600; font-size: 0.8rem; display: flex; align-items: center; gap: 8px;">
                        <span style="width: 10px; height: 10px; background: #EA580C; border-radius: 50%;"></span>
                        ICICI Bank
                      </button>
                      <button class="rzp-bank-select-btn" data-bank="State Bank of India" style="padding: 10px; border: 1px solid #CBD5E1; border-radius: 8px; background: #F8FAFC; text-align: left; cursor: pointer; font-weight: 600; font-size: 0.8rem; display: flex; align-items: center; gap: 8px;">
                        <span style="width: 10px; height: 10px; background: #2563EB; border-radius: 50%;"></span>
                        State Bank of India
                      </button>
                    </div>
                  </div>

                  <!-- Tab Content: Cards -->
                  <div id="rzp-tab-cards" class="rzp-tab-content" style="display: none;">
                    <div style="font-size: 0.75rem; font-weight: 600; color: #475569; margin-bottom: 8px;">Add a new card</div>
                    <div style="border: 1px solid #CBD5E1; border-radius: 8px; overflow: hidden; margin-bottom: 12px;">
                      <input type="text" class="form-input" placeholder="Card Number (4111 1111 1111 1111)" style="border: none; border-bottom: 1px solid #E2E8F0; border-radius: 0; padding: 10px;" value="4111 1111 1111 1111" />
                      <div style="display: flex;">
                        <input type="text" class="form-input" placeholder="MM / YY" style="border: none; border-right: 1px solid #E2E8F0; border-radius: 0; padding: 10px; width: 50%;" value="12/28" />
                        <input type="password" class="form-input" placeholder="CVV" style="border: none; border-radius: 0; padding: 10px; width: 50%;" value="123" />
                      </div>
                    </div>
                    <label style="font-size: 0.75rem; color: #64748B; display: flex; align-items: center; gap: 6px;">
                      <input type="checkbox" checked /> Save card as per RBI guidelines
                    </label>
                  </div>

                  <!-- Tab Content: Wallet / UPI -->
                  <div id="rzp-tab-wallet" class="rzp-tab-content" style="display: none;">
                    <div style="font-size: 0.75rem; font-weight: 600; color: #475569; margin-bottom: 8px;">Popular Wallets & UPI</div>
                    <div style="display: flex; flex-direction: column; gap: 8px;">
                      <button class="rzp-wallet-btn" style="padding: 10px; border: 1px solid #CBD5E1; border-radius: 8px; background: #F8FAFC; text-align: left; cursor: pointer; font-weight: 600; font-size: 0.8rem;">Google Pay / PhonePe UPI</button>
                      <button class="rzp-wallet-btn" style="padding: 10px; border: 1px solid #CBD5E1; border-radius: 8px; background: #F8FAFC; text-align: left; cursor: pointer; font-weight: 600; font-size: 0.8rem;">Paytm Wallet / Mobikwik</button>
                    </div>
                  </div>
                </div>

                <!-- Submit Action Button -->
                <div>
                  <button id="rzp-continue-btn" style="width: 100%; background: #1E293B; color: #FFFFFF; padding: 12px; border: none; border-radius: 8px; font-weight: 700; font-size: 0.9rem; cursor: pointer; transition: background 0.2s;">
                    Proceed to Pay $${displayAmount}
                  </button>
                </div>
              </div>
            </div>
          </div>
        `;

        overlay.classList.add('show');
        overlay.classList.add('active');

        // Close Handler
        document.getElementById('rzp-close-btn').onclick = () => {
          overlay.classList.remove('show');
          overlay.classList.remove('active');
          if (typeof onError === 'function') onError('Payment cancelled by user');
        };

        // Tab Switching
        document.querySelectorAll('.rzp-tab-btn').forEach(btn => {
          btn.addEventListener('click', () => {
            document.querySelectorAll('.rzp-tab-btn').forEach(b => {
              b.style.color = '#64748B';
              b.style.borderBottom = 'none';
            });
            btn.style.color = '#0D9488';
            btn.style.borderBottom = '2px solid #0D9488';

            document.querySelectorAll('.rzp-tab-content').forEach(c => c.style.display = 'none');
            const target = btn.getAttribute('data-tab');
            document.getElementById(`rzp-tab-${target}`).style.display = 'block';
          });
        });

        // Bank Select Button Handler -> Opens Screen 2 (Razorpay Software Private Ltd Bank Mock Page)
        document.querySelectorAll('.rzp-bank-select-btn').forEach(btn => {
          btn.addEventListener('click', () => {
            const bankName = btn.getAttribute('data-bank');
            renderScreen2(bankName);
          });
        });

        // Continue Button Handler
        document.getElementById('rzp-continue-btn').onclick = () => {
          renderScreen2('Razorpay Software Private Ltd Bank');
        };
      };

      // Screen 2: Demo Bank Gateway Mock Page (Matches User's Screenshot 2)
      const renderScreen2 = (bankName) => {
        overlay.innerHTML = `
          <div class="modal-card rzp-demo-bank-modal" style="max-width: 650px; width: 90%; background: #FFFFFF; border-radius: 12px; overflow: hidden; box-shadow: 0 25px 50px rgba(0,0,0,0.25); font-family: sans-serif;">
            <div style="background: #1E293B; color: #FFFFFF; padding: 10px 16px; font-size: 0.8rem; display: flex; align-items: center; gap: 8px;">
              <span style="width: 12px; height: 12px; background: #22C55E; border-radius: 50%;"></span>
              <span><strong>Razorpay Bank Gateway</strong> &bull; api.razorpay.com/v1/gateway/mocksharp/payment?key_id=${global.DealFlowConfig.RAZORPAY_KEY_ID}</span>
            </div>

            <div style="padding: 48px 32px; text-align: center;">
              <div style="font-size: 4rem; font-weight: 800; color: #0284C7; font-style: italic; margin-bottom: 16px;">1</div>
              <h2 style="font-size: 1.3rem; font-weight: 700; color: #0F172A; margin: 0 0 12px;">Welcome to ${bankName}</h2>
              <p style="font-size: 0.9rem; color: #64748B; margin-bottom: 32px;">
                This is just a demo bank page.<br />You can choose whether to make this payment successful or not:
              </p>

              <div style="display: flex; justify-content: center; gap: 16px;">
                <button id="rzp-bank-success-btn" style="background: #22C55E; color: #FFFFFF; border: none; padding: 12px 36px; border-radius: 6px; font-weight: 700; font-size: 1rem; cursor: pointer; transition: transform 0.1s;">
                  Success
                </button>
                <button id="rzp-bank-failure-btn" style="background: #EF4444; color: #FFFFFF; border: none; padding: 12px 36px; border-radius: 6px; font-weight: 700; font-size: 1rem; cursor: pointer; transition: transform 0.1s;">
                  Failure
                </button>
              </div>
            </div>
          </div>
        `;

        // Success Handler -> Screen 3 (Processing spinner)
        document.getElementById('rzp-bank-success-btn').onclick = () => {
          renderScreen3();
        };

        // Failure Handler
        document.getElementById('rzp-bank-failure-btn').onclick = () => {
          overlay.classList.remove('show');
          overlay.classList.remove('active');
          if (typeof onError === 'function') onError('Payment rejected by bank authority.');
        };
      };

      // Screen 3: Processing Your Payment Modal (Matches User's Screenshot 3)
      const renderScreen3 = () => {
        overlay.innerHTML = `
          <div class="modal-card rzp-processing-modal" style="max-width: 520px; width: 90%; background: #FFFFFF; border-radius: 12px; padding: 40px; text-align: center; box-shadow: 0 25px 50px rgba(0,0,0,0.25);">
            <h2 style="font-size: 1.4rem; font-weight: 800; color: #0F172A; margin: 0 0 8px;">Processing your payment</h2>
            <p style="font-size: 0.85rem; color: #64748B; margin-bottom: 28px;">This will only take a few seconds.</p>

            <div style="margin: 24px 0; display: flex; justify-content: center;">
              <div style="width: 56px; height: 56px; border-radius: 50%; background: #FEF08A; border: 3px solid #EAB308; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; font-weight: 800; color: #CA8A04; animation: pulse 1s infinite alternate;">
                $
              </div>
            </div>

            <div style="font-size: 0.75rem; color: #94A3B8; margin-top: 20px;">
              Verifying Razorpay HMAC signature and updating invoice settlement ledger...
            </div>
          </div>
        `;

        // Automatically complete signature verification & record payment after 1.2s
        setTimeout(async () => {
          try {
            const payId = `pay_${Date.now()}`;
            const mockSig = `mock_sig_${Date.now()}`;

            const verifyRes = await global.PaymentsAPI.verifyRazorpayPayment({
              razorpay_order_id: order_id,
              razorpay_payment_id: payId,
              razorpay_signature: mockSig,
              customer_id: customer_id || 1,
              invoice_id: invoice_id,
              amount: Number(amount),
              currency: currency
            });

            overlay.classList.remove('show');
            overlay.classList.remove('active');

            if (typeof onSuccess === 'function') {
              onSuccess({
                razorpay_payment_id: payId,
                razorpay_order_id: order_id,
                razorpay_signature: mockSig,
                record: verifyRes
              });
            }
          } catch (err) {
            overlay.classList.remove('show');
            overlay.classList.remove('active');
            if (typeof onError === 'function') onError(err.message || 'Razorpay signature verification failed.');
          }
        }, 1200);
      };

      // Launch Screen 1
      renderScreen1();
    }
  };

  global.RazorpayGatewayModal = RazorpayGatewayModal;
})(typeof window !== 'undefined' ? window : this);
