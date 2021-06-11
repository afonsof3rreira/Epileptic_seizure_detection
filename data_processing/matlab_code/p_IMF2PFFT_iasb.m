% FF spectrum of matrix signals as IMFs
function p_IMF2PFFT_simple(IMF,Fs, fig_name, func_name, signal_label)

sup_str = strcat('Signal $\,$', signal_label, ...
                 ': $\,$ single-Sided Amplitude Spectrum of Mode(t) $|$FFT(f)$|$ using $\,$',...
                 func_name);
str_decomps = 'IMF';

[N L] = size(IMF);
if (nargin == 1) Fs = 256; end  % Sampling frequency                    
T = 1/Fs;                       % Sampling period       
t = (0:L-1)*T;                  % Time vector
f = Fs*(0:(L/2))/L;

fig_str = strcat(fig_name, '-FFT-', func_name, '-', signal_label);
figure('Name', fig_str, 'Position', [353,34,560,663]);


    
decomp_strs = cell(1, N);

for i = 1:N
    Y = fft(IMF(i,:));
    P2 = abs(Y/L);
    P1 = P2(1:L/2+1);
    P1(2:end-1) = 2*P1(2:end-1);
    subplot(N,1,i);
    plot(f,P1);
    xlim([1 5]);
    grid on;
    title_str_i = strcat(str_decomps, num2str(i));
    title(title_str_i,...
      'interpreter','latex','FontUnits','points',...
      'FontWeight','demi','FontSize',8,'FontName','Times');
    decomp_strs{i} = convertStringsToChars(title_str_i);
    PFFT(i,:) = P1;
end
%set(gca,'xtick',[],'FontSize',8,'XLim',[0 L]);
xlabel('f $[Hz]$','interpreter','latex','FontUnits',...
        'points','FontWeight','normal','FontSize',10,'FontName',...
        'Times');
    
sgtitle(sup_str,...
        'interpreter','latex','FontUnits','points',...
        'FontWeight','demi','FontSize',8,'FontName','Times');
end