# Osiloskop üzerinde vektörel resim çizdirme

Bu dosya `REPORT.md` dosyasının Türkçe okuma kopyasıdır. Asıl rapor İngilizcedir.

## 1. Giriş

Bu projede osiloskop kullanmayı, RC devresi kurmayı ve bir PWM çıkışını bu RC
devresiyle birlikte kullanarak DAC'ı, yani dijital analog çeviriciyi taklit etmeyi
öğrendim.

### 1.1 Projenin amacı

Amaç, bir osiloskopta XY modunda anlamlı bir vektörel görsel elde etmektir;
görsel, kartın kendi ürettiği bir nokta listesinden çizilir. XY modunda ekrandaki
nokta, cihazın kendi ürettiği bir zaman taramasıyla değil, iki giriş gerilimiyle
konumlandırılır. Raspberry Pi Pico 2 bu iki gerilimi üretir ve noktayı bir yol
boyunca, gözün bütün bir resim gördüğü hızda gezdirir.

Tasarımı cihazın tek bir özelliği belirler. XY modunda çerçeve belleği (frame
buffer) yoktur. Bilgisayar ekranı bir piksel ızgarasını bellekte tutar ve hepsini
tazeler; osiloskop hiçbir şey saklamaz. Ekranda tek bir nokta vardır ve o
noktanın nerede durduğu yalnızca şu anda mevcut olan iki gerilime bağlıdır. Bu
yüzden bir resim, noktanın sırayla ziyaret ettiği tek ve sıralı bir nokta
listesidir.

Pico 2'nin analog çıkışı yoktur, dolayısıyla bu iki gerilimi doğrudan üretemez.
Her iki eksen de bir PWM sinyalinin RC ağından geçirilip süzülmesiyle elde edilir.

### 1.2 Osiloskop kullanımı

Osiloskop bir gerilim grafiği çizer. Normal modunda yatay eksen zaman, düşey
eksen prob ucundaki gerilimdir; sinyalin zaman içinde değişen şeklini gösterir. Bu
eşlemeyi belirleyen ayarlar şunlardır:

- Bölme başına gerilim (V/div) düşey ölçeği belirler. Daha uzun bir iz daha büyük
  bir gerilim demektir.
- Bölme başına zaman (time/div) taramanın ekranı ne kadar hızlı geçtiğini
  belirler.
- Kuplaj seçimi DC ise sinyalin ortalama seviyesi dahil tamamı geçer; AC ise
  ortalama engellenir ve yalnızca değişim görünür.
- Giriş empedansı, burada 1 Mohm, probun ölçülen devreye gösterdiği dirençtir.
  Bu değerin yüksek olması cihazın ölçtüğü devreyi yüklememesini sağlar.
- Tetikleme (trigger) bir taramanın ne zaman başlayacağına karar verir. Tekrar
  eden bir dalga şeklinin ekranda kaymak yerine sabit durmasını sağlayan şey
  budur.

### 1.3 Neden RC filtresi kullanıyoruz

Pico'nun GPIO pini dijital bir çıkıştır. 0 V veya 3.3 V tutabilir, ikisinin
arasında hiçbir değer veremez. Oysa çizim, her eksende düzgün biçimde değişebilen
bir gerilim ister. Bu boşluk, pini çok hızlı açıp kapatarak ve sonucun
ortalamasını alarak kapatılır. Ortalamayı alan eleman bir direnç ile bir
kondansatördür. Aynı elemanlar ayrıca noktanın ne kadar hızlı hareket
edebileceğini de belirler, bu da bir resmin kaç nokta içerebileceğine üst sınır
koyar.

## 2. Teori

### 2.1 Osiloskop nasıl çalışır

Bu projede kullanılan cihaz dijital osiloskoptur. Ekranı bir LCD'dir; elektron
tabancası, saptırma plakası ve fosfor yoktur. Her giriş kanalının kendi analog
dijital çeviricisi vardır. Çevirici, prob ucundaki gerilimi cihazın örnekleme
hızında sayısallaştırır ve örnekler yakalama belleğine yazılır. Ekranda görünen
her şey, bellekteki bu sayılardan yeniden kurulur.

Normal çalışmada cihaz her örneği kayıt içindeki sırasına karşı çizer: yatay eksen
zaman, düşey eksen ölçülen gerilimdir.

XY modu bu eşlemeyi değiştirir. Zaman artık bir eksen değildir. Cihaz, aynı ana
ait iki örneği, yani kanal 1'den ve kanal 2'den geleni, tek bir noktanın yatay ve
düşey koordinatı olarak alır. Her örnek çifti ekranda bir nokta olur. Bu cihaza
yeterince hızlı bir koordinat listesi vermek bir çizim üretir. Cihazın yakaladığı
zaman penceresi, çizimin en az bir tam turunu kapsamalıdır; kapsamazsa ekranda
şeklin yalnızca bir parçası görünür. Cihazın kendi örnekleme hızı da, gönderilen
nokta hızına göre yeterince yüksek olmalıdır, yoksa ardışık noktalar birbirinden
ayırt edilemez.

### 2.2 Darbe genişlik modülasyonu (PWM)

Darbe genişlik modülasyonu, kısaca PWM, analog bir değeri dijital bir çıkış
üzerinden taşıma yöntemidir. Pin, periyodu T olan sabit bir kare dalga üretir. Her
periyot içinde t_on kadar süre yüksekte, kalan sürede alçakta kalır. Şu oran

    D = (t_on / T)

görev çevrimi (duty cycle) olarak adlandırılır ve 0 ile 1 arasında değişir.
Sinyalin kendisi hâlâ yalnızca 0 V veya 3.3 V'tur, ancak bir periyot boyunca
ortalaması

    V_avg = (D * V_besleme)

olur. Yani 0.5 görev çevrimi 1.65 V'a, 0.25 görev çevrimi 0.825 V'a karşılık
gelir. Görev çevrimini değiştirmek ortalamayı değiştirir ve arkadan gelen
filtrenin süzüp çıkaracağı değer de bu ortalamadır.

Bir PWM kanalını iki sayı tanımlar. Çözünürlük, görev çevriminin ne kadar ince
ayarlanabildiğidir ve bit cinsinden ifade edilir; bu projede 16 bitlik görev
çevrimi değerleri yazılır, bu da aralığı 65536 kademeye böler. Taşıyıcı frekans
ise 1 / T değeridir ve temsil edilen sinyalin frekansının çok üstünde olmalıdır ki
filtre ikisini birbirinden ayırabilsin. Filtrenin temizleyemediği artık
anahtarlama, çıkışta dalgalanma (ripple) olarak görünür.

### 2.3 Dijital analog çevirici (DAC)

Dijital analog çevirici, kısaca DAC, bir yazmaçta tutulan sayıyı orantılı bir
gerilime dönüştürür. Mikrodenetleyicinin gerilim okumak için kullandığı ADC'nin
tersidir. Bir DAC şu üç büyüklükle tanımlanır: çözünürlük, yani bit sayısı ve
dolayısıyla üretebildiği farklı çıkış seviyesi sayısı; örnekleme hızı, yani
saniyede kaç yeni değer kabul ettiği; ve oturma süresi, yani bir değer
yazıldıktan sonra çıkışın o değere varması için geçen zaman.

Adanmış DAC donanımı her giriş koduna doğrudan bir çıkış seviyesi üretir. Bir PWM
pini ile arkasına konan alçak geçiren filtre aynı işi iki pasif elemanla yapar ve
buna PWM DAC denir. Pin iki seviye arasında anahtarlar, filtre ortalamayı süzer,
pine yazılan görev çevrimi de o ortalamayı belirler. Bedeli şudur: çözünürlük,
dalgalanma ve oturma hızı, filtre ile taşıyıcı frekans üzerinden birbirine takas
edilir.

### 2.4 RC alçak geçiren devre

Her eksende kullanılan filtre, sinyale seri bağlı bir direnç ve çıkış düğümünden
toprağa giden bir kondansatörden oluşur; çıkış kondansatörün üzerinden alınır. Bu,
birinci dereceden alçak geçiren filtredir. Yavaş değişimleri geçiren, hızlı
değişimleri bastıran en basit devredir.

Davranışını tek bir büyüklük belirler, zaman sabiti

    tau = (R * C)

Giriş 0'dan yeni bir seviyeye basamak şeklinde sıçrarsa çıkış onu anında izlemez.
Yeni seviyeye üstel bir eğri boyunca yaklaşır

    v(t) = V_son * (1 - exp(-t / tau))

Bu eğri bir tau sonunda basamağın %63.2'sine, iki tau sonunda %86.5'ine, üç tau
sonunda %95.0'ine ulaşır. Frekans düzleminde aynı devrenin bir kesim frekansı
vardır

    f_c = 1 / (2 * pi * R * C)

Bu frekans, çıkış gücünün girişin yarısına düştüğü, yani 3 dB azaldığı nokta
olarak tanımlanır. Kesimin üzerinde yanıt dekad başına 20 dB düşer.

Her iki tanım da burada önemlidir ve ikisi ters yönlere çeker. Devreye frekans
filtresi olarak bakıldığında, anahtarlamanın temiz bir ortalamaya
yumuşatılabilmesi için kesim frekansının PWM taşıyıcısının epey altında olması
gerekir; büyük tau bunu daha iyi yapar. Aynı devreye basamak yanıtı olarak
bakıldığında ise çıkışın, çizimin bir noktasından diğerine, o noktaya ayrılan süre
içinde varması gerekir; büyük tau bunu daha kötü yapar. R ve C seçmek, düzgün bir
çıkış ile hızlı bir çıkış arasında bir yer seçmek demektir.

Bu projede her iki eksende R = 2.2 kohm ve C = 4.7 nF kullanılmıştır. Bunlar şu
değerleri verir:

    tau = (2200 ohm * 4.7 nF) = 10.34 us
    f_c = 1 / (2 * pi * 2200 * 4.7e-9) = 15.4 kHz

Ana yazılımın kullandığı saniyede 32000 nokta hızında her nokta 31.25 us sürer, bu
da 3.02 tau eder. Dolayısıyla çıkış, bir sonraki koordinat gelmeden önce her yeni
koordinatın %95.1'ine oturur.

### 2.5 Doğrudan bellek erişimi (DMA)

Doğrudan bellek erişimi, kısaca DMA, bellek ile bir çevre birimi arasında veriyi,
her aktarım için işlemciye komut çalıştırtmadan taşıyan donanımdır.

DMA olmadan, bir çevre birimine değer akışı göndermek işlemcinin işidir. İşlemci
bellekten bir değeri yazmaca yükler, o yazmacı çevre birimine yazar, bir sonraki
değere geçer ve bunu tekrarlar. Her değer için bu dizinin bir kez işlemesi
gerekir, dolayısıyla değerlerin çevre birimine ulaşma hızını programın çalışma
hızı belirler.

DMA denetleyicisine ise bir kaynak adresi, bir hedef adresi ve bir öğe sayısı
verilir; aktarımları kendisi yapar. Bu sırada işlemci serbesttir. Bu düzenin
buradaki iki özelliği önemlidir. Aktarım hızını çevre birimi yönetir, çünkü bir
sonraki öğeyi kabul etmeye hazır olduğunda kendisi ister; böylece zamanlama artık
programın hızına bağlı değildir. İkincisi, denetleyici tamponun sonuna
ulaştığında başa dönecek şekilde ayarlanabilir; bu da aynı bellek bloğunu, ona
başka hiçbir şey yazılmadan sonsuza kadar tekrarlar.

## 3. Devre

![İki kanallı RC filtre şeması](schematic.png)

Yukarıdaki şema projenin analog kısmının tamamıdır. Her eksene bir tane olmak
üzere iki kanal vardır ve bu kanallar birbirinin aynısı ve birbirinden
bağımsızdır.

Her kanal üç elemandan kurulur. X ekseni için V1, Y ekseni için V2 olan darbe
kaynağı, mikrodenetleyici pininin yerini tutar; kart üzerinde bunlar 2.2
bölümünde anlatılan PWM kare dalgasını üreten GP2 ve GP3 pinleridir. Bu kaynağa
seri olarak 2.2 kohm'luk bir direnç bağlanır. Direncin öbür ucundan toprağa
4.7 nF'lık bir kondansatör iner. X için J1, Y için J2 olan çıkış konnektörü,
direnç ile kondansatör arasındaki düğümden alınır.

Devrede doğru kurulması gereken tek nokta işte bu düğümdür. Osiloskop probu da,
Pico'nun kendi çıkışını geri okumak için kullandığı ADC ucu da buraya bağlanır.
Bunlardan herhangi birini direncin GPIO tarafına bağlamak kondansatörü devre dışı
bırakır ve ekrana ham kare dalgayı getirir.

İki kanal tek bir toprağı paylaşır; osiloskobun toprak klipsleri de buraya gider.

## 4. Yöntem

### 4.1 Sinyal yolu

Koordinat listesini ekrandaki resme çeviren zincir beş aşamalıdır. Altıncı bir dal
yalnızca ölçüm için kullanılır:

```
koordinat listesi -> 16 bit duty degerleri -> DMA -> PWM (GP2, GP3) -> RC filtre -> osiloskop
                                                                          |
                                                                          +-> ADC (GP26, GP27) -> USB -> Mac izleyici
```

Ekrandaki resmi tamamen kart üretir. Mac'e giden dal tek yönlüdür ve yalnızca
ölçüm içindir; kart bir kez programlandıktan sonra bilgisayar olmadan da çizmeye
devam eder.

DMA aşamasının solundaki her şey açılışta bir kez yapılır. Çizim, her iki eksende
-1 ile 1 arasında değişen kayan noktalı koordinatlarla kurulur, sonra PWM
donanımının istediği tam sayı aralığına çevrilir. `cat_xy.py` içindeki dönüşüm
şudur:

    duty = int((((v + 1.0) * 0.5) * 65535))

Bu ifade her koordinata uygulanır ve -1 değerini 0 duty'sine, +1 değerini 65535
duty'sine eşler. İki eksen daha sonra tek bir `array.array("H")` tamponunda,
nokta başına önce X sonra Y gelecek şekilde iç içe dizilir.

Bu iç içe dizilim, stereo bir ses tamponunun zaten sahip olduğu bellek düzenidir
ve bir sonraki aşamayı mümkün kılan da budur.

### 4.2 Çıkışı DMA ile sürmek

İlk çalışan sürüm duty değerlerini sıradan bir Python döngüsünden iki
`pwmio.PWMOut` nesnesine yazıyordu. Çalışıyordu, ancak CPU 231 noktalı yolu
saniyede ancak 20 ila 40 kez tamamlayabiliyordu ve resim gözle görülür biçimde
titriyordu. Bundan sonrası için çalışma eşiği saniyede 50 tur alınmıştır; 6. ve 7.
bölümlerdeki nokta bütçesi bu eşikten türetilmiştir.

Çözüm, CPU'yu çizim döngüsünden tamamen çıkarmak, yani 2.5 bölümünde anlatılan
DMA'yı kullanmaktır. CircuitPython doğrudan bir DMA arayüzü sunmaz. Buna karşılık
ses çıkışı sunar; ses çıkışı DMA ile sürülür, stereodur ve 16 bitlik örneklerden
oluşan bir tampondan beslenir. Bu yüzden ses yolu, ses üretmek için değil DMA
motoru olarak kullanılır:

```python
sample = audiocore.RawSample(frame, channel_count=2, sample_rate=SAMPLE_RATE)
audio = audiopwmio.PWMAudioOut(left_channel=board.GP2, right_channel=board.GP3)
audio.play(sample, loop=True)
```

Sol kanal X'i, sağ kanal Y'yi taşır. `RawSample`, 4.1 bölümündeki iç içe dizilmiş
tamponu sarmalar; `sample_rate` ise ışının saniyede kaç nokta ziyaret edeceğini
belirler. `loop=True` tamponu başka hiçbir komut gerekmeden sonsuza kadar
tekrarlar, dolayısıyla `play()` geri döndükten sonra çizim CPU hiç karışmadan
devam eder.

Bu yüzden her firmware dosyası boş bir `while True: pass` döngüsüyle biter. Döngü
hiçbir iş yapmaz; yalnızca `code.py` dosyasının sonuna varmasını engeller, çünkü
CircuitPython program bittiğinde çıkışları kapatır. CPU o andan itibaren boştadır.

## 6. Sonuçlar

### 6.2 Ölçülen değerler

Gerilimler, Pico'nun GP26 ve GP27 üzerinden kendi çıkışlarını okumasıyla
ölçülmüştür. "türetilmiş" işaretli değerler doğrudan gözlenmemiş, ölçülen
değerlerden hesaplanmıştır.

| Büyüklük | Değer | Kaynak |
| --- | --- | --- |
| RC zaman sabiti, `(R * C)` | 10.34 us | türetilmiş |
| RC kesim frekansı | 15.4 kHz | türetilmiş |
| Örnekleme hızı | 32000 nokta/s | ayarlanan |
| Nokta başına süre | 31.25 us = 3.02 tau | türetilmiş |
| Nokta başına oturma | %95.1 | türetilmiş |
| Yol uzunluğu | 231 nokta | ayarlanan |
| Kare hızı | 138.5 Hz | ölçülen |
| 50 Hz'de nokta bütçesi | 640 nokta | türetilmiş |
| X çıkışı, ortalama / min / maks | 1.696 / 0.426 / 2.850 V | ölçülen |
| Y çıkışı, ortalama / min / maks | 1.725 / 0.562 / 3.226 V | ölçülen |
| ADC hızı, liste üreteci ölçütü | 52206 çift/s | ölçülen |
| ADC hızı, akış firmware'inde pratikte | 43900 çift/s | ölçülen |
| USB akış verimi | yaklaşık 144 kB/s, 18 kare/s | ölçülen |

Sonuç, 231 noktalık bir yolun saniyede 138.5 kez yeniden çizilmesidir; aynı
donanımda 4.2 bölümünde anlatılan Python döngüsü bunu 20 ila 40 kez yapıyordu.
