# Osiloskop üzerine vektör görüntü çizmek

## 1. Giriş

Bu projede osiloskobun nasıl kullanıldığını, bir RC devresinin nasıl kurulduğunu
ve bir PWM çıkışının o RC devresiyle birlikte bir DAC'ı, yani sayısaldan analoğa
çeviriciyi nasıl taklit edebildiğini öğrendim.

### 1.1 Projenin amacı

Bu projeye üç şeyi öğrenmek için başladım: bir RC devresini nasıl kuracağımı ve
ne yapacağını önceden nasıl kestireceğimi, bir osiloskobu nasıl kurup nasıl
okuyacağımı, ve darbe genişlik modülasyonunun yalnızca açık ya da kapalı
olabilen bir pini nasıl ayarlanabilir bir gerilime dönüştürdüğünü. Hedef olarak
ekranda bir resim seçildi, çünkü resim gözle görülür biçimde bozulur. Filtre
yanlışsa çizim yayılır, nokta hızı yanlışsa titrer, yol yanlışsa şekil yanlış
çıkar; yani ekranda kedi gibi bir şey görünmesi için üç konunun da aynı anda
doğru olması gerekir.

Amaç, kartın kendi ürettiği bir nokta listesinden yola çıkarak osiloskobun XY
kipinde anlamlı bir vektör görüntü üretmek. XY kipinde ekrandaki nokta, içeriden
gelen bir zaman süpürmesiyle değil, iki giriş gerilimiyle konumlandırılır. İki
gerilimi bir Raspberry Pi Pico 2 üretir ve noktayı, göz resmin tamamını görecek
kadar hızlı bir şekilde yol boyunca gezdirir.

Tasarımı cihazın tek bir özelliği belirliyor. XY kipinin çerçeve belleği yoktur.
Bir bilgisayar ekranı piksellerden oluşan bir ızgarayı saklar ve hepsini
tazeler; osiloskop hiçbir şey saklamaz. Tek bir nokta gösterir ve o noktanın
nerede durduğu yalnızca o andaki iki gerilime bağlıdır. Dolayısıyla bir resim,
noktanın sırayla ziyaret ettiği tek ve sıralı bir nokta listesidir.

Pico 2'nin analog çıkışı yok, yani bu iki gerilimi doğrudan üretemez. İki eksen
de bir PWM sinyalinin bir RC ağından süzülmesiyle üretiliyor.

### 1.2 Osiloskop kullanımı

Osiloskop gerilimin grafiğini çizer. Normal kipinde yatay eksen zaman, dikey
eksen prob ucundaki gerilimdir; yani ekranda sinyalin zamanla değişen biçimi
görünür. Bu eşleşmeyi ayarlayan kontroller şunlardır:

- Bölme başına volt, dikey ölçeği belirler; daha uzun bir iz daha büyük bir
  gerilim demektir.
- Bölme başına zaman, süpürmenin ekranı ne kadar hızlı geçtiğini belirler.
- Giriş empedansı, burada 1 Mohm, probun ölçülen devreye gösterdiği dirençtir.
  Yüksek bir değer, cihazın ölçtüğü devreyi yüklemesini engeller.
- Tetikleme, bir süpürmenin ne zaman başlayacağına karar verir; tekrarlayan bir
  dalga biçiminin ekranda kaymak yerine sabit durmasını sağlayan şey budur.

### 1.3 RC filtresi neden kullanılıyor

Pico üzerindeki bir GPIO pini sayısal bir çıkıştır. 0 V ya da 3.3 V tutabilir,
arada hiçbir şey tutamaz; oysa çizim her eksende düzgün biçimde değişen bir
gerilime ihtiyaç duyar. Bu boşluk, pini çok hızlı açıp kapatarak ve sonucun
ortalamasını alarak kapatılır. Ortalamayı bir direnç ve bir kondansatör alır ve
aynı elemanlar noktanın ne kadar hızlı hareket edebileceğini de belirler; bu da
bir resmin kaç nokta içerebileceğine bir üst sınır koyar.

## 2. Teori

### 2.1 Osiloskop nasıl çalışır

Bu projede kullanılan cihaz sayısal bir osiloskop. Ekranı bir LCD; elektron
demeti, saptırma plakası ya da fosfor yok. Her giriş kanalının kendi analogdan
sayısala çeviricisi var. Çevirici, prob ucundaki gerilimi cihazın örnekleme
hızında sayısallaştırır ve örnekler toplama belleğine yazılır. Ekranda görünen
her şey, saklanan bu sayılardan yeniden kurulur.

Normal çalışmada cihaz her örneği kayıttaki konumuna karşı çizer: yatay eksen
zaman, dikey eksen ölçülen gerilimdir.

XY kipi bu eşleşmeyi değiştirir. Zaman artık bir eksen değildir. Cihaz aynı ana
ait iki örneği, biri 1. kanaldan biri 2. kanaldan, alır ve bunları tek bir
noktanın yatay ve dikey koordinatı olarak yorumlar. Her örnek çifti ekranda bir
nokta olur. Cihaza yeterince hızlı bir koordinat listesi vermek bir çizim
üretir. Cihazın yakaladığı zaman penceresinin, çizimin en az bir tam turunu
kapsaması gerekir; aksi halde şeklin yalnızca bir kısmı görünür. Cihazın kendi
örnekleme hızının da, noktaların gönderilme hızına göre yeterince yüksek olması
gerekir; yoksa ardışık noktalar birbirinden ayırt edilemez.

### 2.2 Darbe genişlik modülasyonu

Darbe genişlik modülasyonu, ya da PWM, sayısal bir çıkış üzerinde analog bir
değer taşımanın bir yoludur. Pin, sabit T periyotlu bir kare dalga üretir. Her
periyot içinde t_on süresi boyunca yüksek, geri kalanda alçak kalır. Şu oran

    D = (t_on / T)

görev çevrimi diye adlandırılır ve 0 ile 1 arasında değişir. Sinyalin kendisi
hâlâ yalnızca 0 V ya da 3.3 V'tur, ama bir periyot üzerindeki ortalaması

    V_ort = (D * V_besleme)

olur; yani 0.5 görev çevrimi 1.65 V, 0.25 görev çevrimi 0.825 V ortalamasını
verir. Görev çevrimini değiştirmek ortalamayı değiştirir ve o ortalama, sonraki
filtrenin çekip çıkaracağı değerdir.

Bir PWM kanalını iki sayı tanımlar. Çözünürlük, görev çevriminin ne kadar ince
ayarlanabildiğidir ve bit cinsinden ifade edilir; bu proje 16 bitlik görev
değerleri yazıyor, bu da aralığı 65536 adıma böler. Taşıyıcı frekansı 1 / T'dir
ve temsil edilen sinyalin frekansının çok üstünde olmalıdır ki filtre ikisini
ayırabilsin. Filtrenin temizleyemediği artık anahtarlama, çıkışta dalgalanma
olarak görünür.

### 2.3 Sayısaldan analoğa çevirme

Sayısaldan analoğa çevirici, ya da DAC, bir yazmaçta tutulan sayıyı orantılı bir
gerilime dönüştürür. Bir mikrodenetleyicinin gerilim okumak için kullandığı
ADC'nin tersidir. Bir DAC şu üç şeyle tanımlanır: çözünürlüğü, yani bit sayısı
ve dolayısıyla üretebildiği farklı çıkış seviyesi sayısı; örnekleme hızı, yani
saniyede kaç yeni değer kabul ettiği; ve yerleşme süresi, yani yeni bir değer
yazıldıktan sonra çıkışın o değere ulaşması için geçen süre.

Özel DAC donanımı her giriş koduna karşılık doğrudan bir çıkış seviyesi üretir.
Bir alçak geçiren filtreyle takip edilen bir PWM pini aynı işi iki pasif elemanla
yapar ve buna PWM DAC denir. Pin iki seviye arasında anahtarlar, filtre
ortalamayı çıkarır ve pine yazılan görev çevrimi o ortalamayı belirler. Bedeli
şudur: çözünürlük, dalgalanma ve yerleşme hızı, filtre ve taşıyıcı frekansı
üzerinden birbirine karşı takas edilir.

### 2.4 RC alçak geçiren devresi

Her eksende kullanılan filtre, sinyalle seri bir direnç ile çıkış düğümünden
toprağa inen bir kondansatörden oluşur ve çıkış kondansatörün üzerinden alınır.
Bu, yavaş değişimleri geçirip hızlı olanları bastıran en basit devre olan birinci
dereceden bir alçak geçiren filtredir.

Davranışını tek bir büyüklük belirler: zaman sabiti

    tau = (R * C)

Giriş 0'dan yeni bir seviyeye basamak yaparsa, çıkış onu anında takip etmez.
Yeni seviyeye üstel bir eğri boyunca yaklaşır

    v(t) = V_son * (1 - exp(-t / tau))

bu da bir tau sonunda basamağın % 63.2'sine, iki tau sonunda % 86.5'ine, üç tau
sonunda % 95.0'ine ulaşır. Frekans alanında aynı devrenin bir kesim frekansı
vardır

    f_c = 1 / (2 * pi * R * C)

bu da çıkış gücünün girişin yarısına, yani 3 dB düştüğü nokta olarak tanımlanır.
Kesimin üstünde tepki dekad başına 20 dB düşer.

Her iki tanım da burada önemli ve ikisi ters yönlere çekiyor. Bir frekans
filtresi olarak bakıldığında devrenin kesimi, anahtarlamanın temiz bir ortalamaya
yumuşatılması için PWM taşıyıcısının epey altında olmalı ve büyük bir tau bunu
daha iyi yapar. Basamak tepkisi olarak bakıldığında ise aynı devre, çıkışı bir
noktadan diğerine o noktaya ayrılan süre içinde taşımalı ve büyük bir tau bunu
daha kötü yapar. R ve C seçmek, yumuşak bir çıkışla hızlı bir çıkış arasında bir
yer seçmektir.

Bu proje her iki eksende de R = 2.2 kohm ve C = 4.7 nF kullanıyor, bu da şunları
veriyor

    tau = (2200 ohm * 4.7 nF) = 10.34 us
    f_c = 1 / (2 * pi * 2200 * 4.7e-9) = 15.4 kHz

Ana yazılımın kullandığı saniyede 32000 noktada her nokta 31.25 us sürer, bu da
3.02 tau eder; yani çıkış, bir sonraki koordinat gelmeden önce her yeni
koordinatın % 95.1'ine yerleşir.

### 2.5 Doğrudan bellek erişimi

Doğrudan bellek erişimi, ya da DMA, bellek ile bir çevre birimi arasında, her
aktarım için işlemci bir komut çalıştırmadan veri taşıyan donanımdır.

O olmadan, bir çevre birimine değer akışı göndermek işlemcinin işidir. Bellekten
bir değeri bir yazmaca yükler, o yazmacı çevre birimine yazar, bir sonraki değere
geçer ve tekrarlar. Her değer için bu dizinin bir turu gerekir, yani değerlerin
çevre birimine ulaşma hızını programın ne kadar hızlı çalıştığı belirler.

Bir DMA denetleyicisine ise bir kaynak adresi, bir hedef adresi ve bir öğe sayısı
verilir; aktarımları kendisi yapar. Bu sırada işlemci serbesttir. Bu düzenin iki
özelliği burada önemli. Aktarım hızını çevre birimi yönetir, çünkü bir sonraki
öğeyi kabul etmeye hazır olduğunda ister; yani zamanlama artık programın hızına
bağlı değildir. İkincisi, bir denetleyici tamponun sonuna geldiğinde başa dönecek
şekilde ayarlanabilir; bu da aynı bellek bloğunu, üzerine başka bir şey
yazılmadan sonsuza kadar tekrar oynatır.

## 3. Devre

<img src="schematic.png" alt="İki kanallı RC filtre şeması" width="340">

**Şekil 1.** Projenin analog kısmı.

Şekil 1 projenin analog kısmının tamamı. Her eksene bir tane olmak üzere iki
kanal var; bunlar birbirinin aynısı ve birbirinden bağımsız.

Her kanal üç elemandan kuruluyor. Bir darbe kaynağı, X ekseni için V1 ve Y
ekseni için V2, mikrodenetleyici pinini temsil ediyor; kart üzerinde bunlar
bölüm 2.2'de anlatılan PWM kare dalgasını çıkaran GP2 ve GP3. Bu kaynakla seri
olarak 2.2 kohm'luk bir direnç var. Direncin öbür ucundan toprağa 4.7 nF'lık bir
kondansatör iniyor. Çıkış konnektörü, X için J1 ve Y için J2, direnç ile
kondansatör arasındaki düğümden alınıyor.

Devrede doğru yapılması gereken tek nokta o düğüm. Osiloskop probu oraya
bağlanıyor, Pico'nun kendi çıkışını geri okuduğu ADC ucu da oraya. İkisinden
birini direncin GPIO tarafına bağlamak kondansatörü atlar ve ekrana ham kare
dalgayı koyar.

İki kanal tek bir toprağı paylaşıyor; osiloskop toprak klipsleri de oraya
gidiyor.

## 4. Yöntem

### 4.1 Sinyal yolu

Bir koordinat listesini resme dönüştüren zincirin beş aşaması, artı yalnızca
ölçüm için kullanılan altıncı bir kolu var:

```
koordinat listesi -> 16 bit görev değerleri -> DMA -> PWM (GP2, GP3) -> RC filtre -> osiloskop
                                                                           |
                                                                           +-> ADC (GP26, GP27) -> USB -> Mac görüntüleyici
```

Ekrandaki resmi tamamen kart üretiyor. Mac'e giden kol tek yönlü ve yalnızca
ölçüm için var; kart bir kez programlandıktan sonra bilgisayar bağlı olmadan
çizmeye devam ediyor.

DMA aşamasının solundaki her şey bir kez, açılışta oluyor. Çizim, her iki eksende
-1 ile 1 arasında koordinatlarla kayan noktalı olarak kuruluyor, sonra PWM
donanımının istediği tam sayı aralığına dönüştürülüyor. `livescope_fw.py`
içindeki dönüşüm şu

    duty = int((((v + 1.0) * 0.5) * 65535))

her koordinata uygulanıyor ve -1'i 0 görev değerine, +1'i 65535'e eşliyor. İki
eksen daha sonra tek bir `array.array("H")` tamponunda, nokta başına bir X değeri
ve ardından bir Y değeri olacak şekilde iç içe geçiriliyor.

Bu iç içe geçmiş yerleşim, bir stereo ses tamponunun zaten sahip olduğu bellek
yerleşimi; bir sonraki aşamayı mümkün kılan da bu.

### 4.2 Çıkışı DMA ile sürmek

İlk çalışan sürüm, görev değerlerini sıradan bir Python döngüsünden iki
`pwmio.PWMOut` nesnesine yazıyordu. Çalışıyordu, ama CPU 231 noktalık yolu
saniyede ancak 20 ila 40 kez tamamlayabiliyordu ve resim gözle görülür şekilde
titriyordu. Sabit bir resim için çalışma eşiği olarak saniyede elli tur alınıyor.

Çözüm, bölüm 2.5'te anlatılan DMA'yı kullanarak CPU'yu çizim döngüsünden tamamen
çıkarmak. CircuitPython doğrudan bir DMA arayüzü sunmuyor. Ama DMA ile sürülen,
stereo ve 16 bitlik örneklerden oluşan bir tampondan beslenen ses çıkışını
sunuyor; dolayısıyla ses yolu, ses için değil bir DMA motoru olarak kullanılıyor:

```python
sample = audiocore.RawSample(frame, channel_count=2, sample_rate=SAMPLE_RATE)
audio = audiopwmio.PWMAudioOut(left_channel=board.GP2, right_channel=board.GP3)
audio.play(sample, loop=True)
```

Sol kanal X'i, sağ kanal Y'yi taşıyor. `RawSample`, bölüm 4.1'deki iç içe geçmiş
tamponu sarmalıyor ve `sample_rate`, demetin saniyede kaç nokta ziyaret ettiğini
belirliyor. `loop=True` tamponu başka bir komut gerekmeden sonsuza kadar tekrar
oynatıyor; yani `play()` döndükten sonra çizim, CPU hiç karışmadan sürüyor.

Yalnızca çizim yapan yazılımın boş bir `while True: pass` döngüsüyle bitmesinin
sebebi bu. Döngü hiçbir iş yapmıyor; sadece `code.py`nin sonuna ulaşmasını
engelliyor, çünkü program bittiğinde CircuitPython çıkışları kapatıyor. O
noktadan sonra CPU boşta.

Adları `_livescope_fw.py` ile biten dosyalar iş yapan bir döngüyle bitiyor: ADC
uçlarını okuyup USB'ye paketler yazıyorlar. O döngü bölüm 4.1'deki ölçüm kolu ve
çizimin parçası değil. Resim o olmadan da aynı olurdu; asıl mesele de bu: CPU
çizimle ilgisiz bir işle meşgulken çizim devam ediyor.

## 5. Sonuçlar

<img src="scope_output.jpg" alt="Yaylardan kurulu kedi cihaz üzerinde" width="340">

**Şekil 2.** Yaylardan kurulu kedinin bir Owon SmartDS5032E üzerinde XY kipindeki
çıktısı. Her iki kanal bölme başına 1 V, cihaz 125 kS/s ile örnekliyor, zaman
tabanı bölme başına 4.0 ms.

Şekil 2, devrenin ürettiği şey. Yol kendi üzerine kapanıyor, çizgiler kesintisiz
ve baş, gözler ve burun arasındaki bağlantı çizgileri çizimin bir parçası olarak
görünüyor; bu da demeti karartmanın bir yolu olmamasının sonucu.

<img src="scope_undersampled.jpg" alt="Aynı kart 125 S/s ile toplanmış" width="340">

**Şekil 3.** Aynı çalışan kart, zaman tabanı bölme başına 4 s'ye alınmış; bu da
toplama hızını 125 S/s'ye düşürüyor. Buradaki dikey ölçek bölme başına 500 mV,
bu yüzden şekil ekranın daha büyük bir kısmını kaplıyor.

Şekil 3, aynı kartın aynı şeyi yaptığını gösteriyor; değişen tek şey cihazın
kendi ayarları. Kart hâlâ saniyede 32000 nokta gönderirken cihaz saniyede 125
çift kaydediyor, yani kabaca her (32000 / 125) = 256 çiftten birini tutuyor ve
tuttukları tek bir yol turundan değil, birçok farklı turdan geliyor. Dış hat
birbirine bağlanmayan noktalara ayrılıyor. Bu, bölüm 2.1'de belirtilen ikinci
koşul ve çizimin değil ölçümün bir özelliği.

Şekil 2 ve 3, Tablo 1'in anlattığı yazılım olan 32 kHz'lik yaylardan kurulu kedi.
Aynı cihaz, Şekil 4 ve 5'teki iki 512 kHz'lik çizimi de fotoğraflıyor; orada
nokta hızı on altı kat daha yüksek ve Şekil 3'ün noktalı izi aynı sebeple geri
dönüyor. Dört fotoğrafın hepsi aynı devre; yalnızca yazılım ve cihaz ayarları
değişiyor.

Gerilimler, Pico'nun kendi çıkışlarını GP26 ve GP27 üzerinden okumasıyla ölçüldü.
Türetilmiş olarak işaretlenen değerler doğrudan gözlenmedi, ölçülenlerden
hesaplandı.

Tablo 1, Şekil 2'de fotoğraflanan çalışmayı anlatmıyor. Ölçüm ADC kolunu
gerektirdiği için sayılar `livescope_fw.py`den geliyor; o da aynı yaylardan
kurulu kediyi çiziyor, yolu doğal 231 noktasında bırakıyor ve 138.5 Hz ile yeniden
çiziyor. Şekil 2'deki çalışma, aynı dış hattı eşit aralıklı 400 noktaya yeniden
örnekleyen ve dolayısıyla (32000 / 400) = 80 Hz ile yeniden çizen daha eski bir
varyanttı; o varyant artık depoda tutulmuyor, çünkü çizdiği geometriyi
`livescope_fw.py` zaten taşıyor. Devre, örnekleme hızı ve gerilimler her iki
durumda da aynı.

**Tablo 1.** `livescope_fw.py` için ölçülen, türetilen ve ayarlanan değerler.

| Büyüklük | Değer | Kaynak |
| --- | --- | --- |
| RC zaman sabiti, `(R * C)` | 10.34 us | türetilmiş |
| RC kesim frekansı | 15.4 kHz | türetilmiş |
| Örnekleme hızı | 32000 nokta/s | ayarlanmış |
| Nokta başına süre | 31.25 us = 3.02 tau | türetilmiş |
| Nokta başına yerleşme | % 95.1 | türetilmiş |
| Yol uzunluğu | 231 nokta | yol kurucudan |
| Çerçeve hızı | 138.5 Hz | türetilmiş |
| X çıkışı, ortalama / min / maks | 1.696 / 0.426 / 2.850 V | ölçülmüş |
| Y çıkışı, ortalama / min / maks | 1.725 / 0.562 / 3.226 V | ölçülmüş |

Çerçeve hızı türetilmiş olarak listelenmiş, çünkü bir cihazdan okunmuyor.
Üstündeki iki satırdan, (32000 / 231) = 138.5 Hz olarak çıkıyor ve geçerli,
çünkü DMA, CPU ne yaparsa yapsın tampondaki her noktayı ayarlanan hızda ziyaret
ediyor. Bölüm 4.2'deki Python döngüsünün 20 ila 40 Hz'i ölçülmüştü, çünkü orada
hız kodun ne kadar hızlı çalıştığına bağlıydı ve tampona bakarak kestirilemezdi.
Sonuç işte bu karşıtlık: aynı donanımdaki aynı yol, CPU'dan çıkarılarak sabit
hale getirildi.

### 5.1 Çıkışlar neden 0 ve 3.3 V'a ulaşmıyor

Tablo 1'in iki gerilim satırı doğal bir soru doğuruyor. PWM DAC 0 ile 3.3 V arası
her şeyi üretebilir ve bölüm 4.1, -1 koordinatını 0 görev değerine, +1'i 65535'e
eşliyor; ama X yalnızca 0.426 ile 2.850 V arasını, Y yalnızca 0.562 ile 3.226 V
arasını kapsıyor. Kaybolan bir şey yok. Kedi, içine çizildiği koordinat kutusunu
doldurmuyor, o kadar.

Yol doğrudan ölçülebilir. Köşeleri X ekseninde -0.720 ile 0.720, Y'de -0.620 ile
0.950 arasında uzanıyor; bunları aynı eşlemeden geçirmek devrenin üretmesi
gereken gerilimleri veriyor:

**Tablo 2.** Yol geometrisinden kestirilen gerilimler, Tablo 1'e karşı.

| Büyüklük | Yoldan | Ölçülen | Fark |
| --- | --- | --- | --- |
| X ortalama | 1.690 V | 1.696 V | 6 mV |
| X min / maks | 0.462 / 2.838 V | 0.426 / 2.850 V | 36 / 12 mV |
| Y ortalama | 1.719 V | 1.725 V | 6 mV |
| Y min / maks | 0.627 / 3.217 V | 0.562 / 3.226 V | 65 / 9 mV |

Ortalamalar her iki eksende de 6 mV içinde uyuşuyor; bu, 3.3 V'luk aralığın
yaklaşık % 0.2'si ve hesabın hiçbir kısmı ölçüme uydurulmadı. Yani çıkış, tam
olarak çizimin istediği aralığı kaplıyor.

Uç değerler daha kötü uyuşuyor ve sebebi devredeki bir kusur değil, o sayıların
ne olduğu. Ortalama 3000 örneği ortalıyor, oysa bir minimum ya da maksimum tek
bir örnek. Yani burada güvenilir sayı ortalamadır; minimum ve maksimum ADC
gürültüsünden çok daha fazla etkilenir ve çalışmadan çalışmaya onlarca milivolt
oynar, ortalamalar ise tekrarda 2 mV içinde geri gelir.

## 6. Dış hat çizimini kestirmek ve ölçmek

### 6.1 İkinci çizim filtreden ne istiyor

`cat_outline.py` içindeki kedi dış hattı 368 köşeli kapalı bir yol. Yalnızca köşe
noktaları yetmezdi, çünkü demet kendisine verilen her noktada aynı süreyi
geçiriyor; iki köşeden çizilen uzun bir çizgi kısa olanla aynı demet süresini alır
ve daha sönük çıkar. Bu yüzden `even_spaced_path` çevreyi ölçüyor, köşelerin
listelendiği 0-255 ızgarasında 1687.2 birim, ve boyunca eşit aralıklarla 7200
nokta yerleştiriyor; bu da her 0.2343 birimde bir nokta, ızgara 0-3.3 V'a
eşlendiğinde 3.03 mV demek.

Bu yazılım tamponu saniyede 512000 nokta hızında çalıştırıyor, yani

    nokta başına süre = (1 / 512000) = 1.953 us
    çerçeve hızı = (512000 / 7200) = 71.1 Hz

Önemli olan ilk sayı, çünkü bölüm 2.4'teki zaman sabitinden büyük değil küçük.
Bir nokta artık

    (1.953 us / 10.34 us) = 0.189 tau

sürüyor; bölüm 4'teki ana yazılım ise nokta başına 3.02 tau veriyordu. Filtrenin
hiçbir tek koordinata yerleşmeye şansı yok. Bu, düzeltilmesi gereken bir kusur
değil. Bir noktadan diğerine adım yalnızca 3.03 mV ve bu kadar küçük bir adımı
verilen sürede takip edemeyen bir filtre, aslında komşuları ortalıyor demektir.

Bu, endişe değil bir kestirim veriyor. Çıkışın, kabaca son bir tau'luk yol
boyunca yumuşatılmış hedef dış hat olması gerekir; bu da

    (10.34 us / 1.953 us) = 5.3 nokta = 1.24 birim = 16.1 mV

yani çizilen nokta, çizginin büküldüğü her yerde hedef çizgiden yaklaşık 16 mV
sapmalı, düz olduğu yerde üstünde kalmalı ve en keskin özellikleri, kulak
uçlarını, içeri çekmeli. Her iki eksen de kendilerine söylenenden biraz daha dar
bir aralık kaplamalı.

### 6.2 Geri gelen sonuç

Ölçümü bölüm 4.1'deki geri okuma yolu sağlıyor. `livescope.py`, kartın USB
üzerinden gönderdiği paketi okuyor, aldığı veriden çizimin bir tam turunu buluyor
ve göstermeden önce 7 örneklik bir ortanca filtreden geçiriyor; yani burada çizilen
iz, canlı görüntüleyicinin gösterdiğinin tam olarak aynısı. Bir turun 630 ADC
örnek çifti olduğu ortaya çıktı; saniyede 71.1 tur ile bu saniyede 44800 çift
demek.

<img src="outline_compare.png" alt="Hedef yol ve geri okuma yan yana" width="460"> <img src="cat_outline_scope.jpg" alt="cat_outline.py cihaz üzerinde" width="330">

**Şekil 4.** GP2 ve GP3'e gönderildiği haliyle 7200 noktalık dış hat, aynı dış
hattın GP26 ve GP27 üzerinden geri okunmuş hali ve cihazın XY kipindeki görüntüsü.
Çizilen iki panel volt cinsinden ve aynı eksenlerde, yani aralarındaki fark iki
sinyal arasındaki farktır, ölçekleme etkisi değil. Fotoğraf, aynı yazılımın ADC
yerine cihaz tarafından görülmüş hali; izi Şekil 3'teki sebeple noktalara
ayrılmış, çünkü saniyede 512000 nokta cihazın topladığı hızın çok üstünde.

**Tablo 3.** Dış hat yazılımı için kestirilen ve ölçülen değerler.

| Büyüklük | Değer | Kaynak |
| --- | --- | --- |
| Dış hattaki köşe sayısı | 368 | ayarlanmış |
| Tur başına çizilen nokta | 7200 | ayarlanmış |
| Çevre | 1687.2 birim | türetilmiş |
| Noktalar arası aralık | 0.2343 birim = 3.03 mV | türetilmiş |
| Örnekleme hızı | 512000 nokta/s | ayarlanmış |
| Nokta başına süre | 1.953 us = 0.189 tau | türetilmiş |
| Çerçeve hızı | 71.1 Hz | türetilmiş |
| tau'dan kestirilen yumuşatma | 16.1 mV | türetilmiş |
| Yoldan sapma, ortalama | 15.0 mV | ölçülmüş |
| Yoldan sapma, ortanca | 12.8 mV | ölçülmüş |
| Yoldan sapma, en kötü | 59.5 mV | ölçülmüş |
| X aralığı, hedeflenen ve ölçülen | 3.041 V, 2.995 V | ölçülmüş |
| Y aralığı, hedeflenen ve ölçülen | 3.092 V, 3.033 V | ölçülmüş |
| Tur başına ADC çifti | 630 | ölçülmüş |
| Bu yazılımdaki ADC hızı | 44800 çift/s | türetilmiş |

Ölçülen bir noktanın hedef dış hattın en yakın noktasına ortalama uzaklığı
15.0 mV; yalnızca zaman sabitinden kestirilen 16.1 mV'a karşı. Kestirim R, C ve
örnekleme hızından yapıldı, yakalanan veriye hiçbir şey uydurulmadı; yani filtre
bölüm 2.4'ün dediği gibi davranıyor ve ekranda görünen hata, bileşen değerlerinin
satın aldığı hata. Bu iki sayının yakınlığının ne kadar ağırlık taşıyabileceği
ayrı bir soru ve bölüm 6.3 onu yanıtlıyor: geri okuma kendi başına benzer
büyüklükte bir hata taşıyor, yani bu uyuşma üç haneli bir eşleşmeyi değil, doğru
büyüklük mertebesini gösteriyor.

O sayının büyüklüğü diğer adayı da eliyor. Pico 2'nin ADC'si 12 bitlik, yani
3.3 V'luk aralıkta bir adım

    (3.3 V / 4096) = 0.806 mV

eder. Ölçülen sapma bunun yaklaşık 19 adımı; çeviricinin kaba sayması için
fazlasıyla büyük, filtreyle eşleşecek kadar küçük.

Aralıklar beklendiği gibi daralıyor. X'e 3.041 V kaplaması söylendi, 2.995 V
kaplıyor; 46 mV ya da % 1.5 kayıp. Y'ye 3.092 V söylendi, 3.033 V kaplıyor;
59 mV ya da % 1.9 kayıp. Sebep körelen köşeler ve Şekil 4 bunu doğrudan
gösteriyor: geri okumadaki kulak uçları gönderilenlerden daha yuvarlak, çünkü son
5.3 nokta üzerinden alınan bir ortalama, yolun hemen terk ettiği bir köşeye
ulaşamaz.

En kötü tek sapma, 59.5 mV, gerçekten sol kulağın ucunda; ama büyük sapmaların
geri kalanı köşelerde toplanmak yerine dağınık. Dolayısıyla bölüm 2.4'ün
modelini sınayan sayı ortalama; en kötü durum, filtre gecikmesini 7 örneklik
ortancadan sağ kalan ADC gürültüsüyle karıştırıyor ve tek başına filtrenin ölçümü
olarak okunmamalı.

Şekil 4'ün bir özelliği devreye değil ölçüme ait. Sağdaki panel gözle görülür
şekilde düz basamaklardan kurulu, oysa kart tur başına 7200 nokta çiziyor. ADC,
kartın 7200 nokta çizdiği sürede 630 çift yakalıyor, yani kabaca her

    (7200 / 630) = 11.4

noktadan birini tutuyor ve görüntüleyici bunları düz çizgilerle birleştiriyor.
Çizilen şey, 7200 noktalık bir yolun 630 kenarlı bir çokgeni. Bu, Şekil 3'ü
üreten aynı yetersiz örnekleme; burada osiloskop yerine geri okuma yolunda
karşımıza çıkıyor. Basamakların nerede göründüğünü de açıklıyor: dış hattın düz
bir kesimi, üzerinden geçen bir kirişle birebir üretilir, bu yüzden merdiven
yalnızca eğrilerde, yanaklar boyunca ve kulakların çevresinde görünür.

### 6.3 Osiloskop ile ADC geri okumasının karşılaştırılması

Kartın çıkışına bu raporda iki kez bakılıyor; aynı düğüme dokunan ve ne
görebildikleri konusunda anlaşamayan iki cihazla. Şekil 4 artık aynı yazılım için
ikisini de gösteriyor: fotoğraf osiloskop ekranı, sağdaki panel `livescope.py`nin
çizdiği ADC geri okuması. Hiçbiri diğerinin denetimi değil ve nedenini açıkça
söylemekte fayda var.

Tablo 4 bunu, cihaz ayarları kaydedilmiş iki çalışmayı kullanarak sayısallaştırıyor:
osiloskop sütunu Şekil 2'de fotoğraflanan 32 kHz'lik çalışma, geri okuma sütunu
Şekil 4'ün 512 kHz'lik çalışması. Yani iki sütun farklı nokta hızlarındaki farklı
çizimleri anlatıyor; örnekleme yoğunluğu satırının bu kadar keskin ayrılmasının
sebebi bu. Karşılaştırma iki çizim arasında değil, iki gözlemci arasında.

**Tablo 4.** Çıkışın gözlendiği iki yol.

| | Osiloskop, Şekil 2 | ADC geri okuması, Şekil 4 |
| --- | --- | --- |
| Hız | 125 kS/s | 44800 çift/s |
| Şu hızdaki bir çizime karşı | 32000 nokta/s | 512000 nokta/s |
| Örnekleme yoğunluğu | nokta başına 3.9 örnek | 11.4 noktada 1 çift |
| X ve Y | aynı an | arka arkaya okunuyor |
| Çıktı | bir fotoğraf | sayılar |

Tablonun ilk çözdüğü şey, iki şeklin neden bu kadar farklı göründüğü. Osiloskop,
kartın çizdiği her nokta için yaklaşık dört örnek alıyor, yani ekrandaki şekil
çizimin kendisinden daha yoğun ve kesintisiz görünüyor. ADC ise her 11.4 noktada
bir çift tutuyor, yani geri okuma çizimden daha seyrek ve bir çokgen olarak
görünüyor. Bu, kartta değil gözlemcilerde olan bir fark.

Ölçümü sınırlayan satır ikincisi. Bölüm 2.1, cihazın aynı ana ait iki örneği, her
kanaldan birini, aldığını anlatıyor; bir örnek çiftini nokta yapan şey de bu.
Geri okuma yazılımı bunu yapamıyor. X ve Y değerleri tam olarak aynı anda
okunamadığı için ölçümde küçük bir zaman farkı oluşuyor. Bu fark çift
periyoduyla sınırlı,

    (1 / 44800) = 22.3 us

ve çizim bu süre boyunca yerinde durmuyor. Saniyede 512000 noktada demet bu
sürede 11.4 noktaya kadar yol alır, bu da 2.68 birim yol ya da 34.7 mV eder.

Bu sayı, yanında durduğu şey yüzünden dikkat hak ediyor. Bölüm 6.2, geri okumayı
hedef dış hattan 15.0 mV uzakta ölçtü ve bunu zaman sabitinden kestirilen
16.1 mV ile eşleştirdi. Uyuşma yakın, ama ölçüm yolu filtreyle hiç ilgisi olmayan,
34.7 mV'a kadar çıkan ikinci bir hata kaynağı taşıyor. İkisi basitçe toplanmıyor,
çünkü bu zaman farkı bir noktayı yola dik değil yol boyunca kaydırıyor ve yolun
bir eksen boyunca gittiği yerlerde çok az katkı veriyor; ama bölüm 6.2'nin dürüst okuması
ilk göründüğünden zayıf: filtre modeli doğru büyüklük mertebesini kestiriyor ve
ölçüm bunu iki haneye kadar doğrulayacak kadar temiz değil.

Bunu iyileştirmek devre değil yazılım sorusu. X, sonra Y, sonra tekrar X okuyup
iki X okumasını ortalamak çifti zamanda ortalar ve farkın çoğunu kaldırırdı.

### 6.4 Aynı ölçüm ikinci bir çizimde

Bölüm 6.2 tek bir çizimi ölçtü. Tek bir ölçüm, devrenin ne yaptığını o belirli
kedinin ondan ne istediğinden ayıramaz; bu yüzden aynı yazılım yapısına ikinci
bir resim verildi. Bu ikinci test için `w2aew_outline.py` içinde, W2AEW
yazısından tamamen farklı şekle sahip kapalı bir yol oluşturuldu. Kedinin
368'ine karşı 486 köşesi var, 1687.2'ye karşı 1666.8 birimlik bir çevre ve tamamen farklı bir yön
dağılımı: kelime neredeyse tamamen dikey ve yatay hatlardan oluşuyor, kedi ise
neredeyse tamamen eğrilerden.

İkisinin ortak yanı, filtrenin umursadığı her şey. İkisi de saniyede 512000 nokta
hızında 7200 nokta oynatıyor, yani ikisi de her noktaya 1.953 us, yani 0.189 tau
veriyor ve ikisi de 71.1 Hz ile yeniden çiziyor. Noktalar arası aralık kelime
için (1666.8 / 7200) = 0.2315 birim, kedi için 0.2343 birim çıkıyor; yani 3.00 mV
karşı 3.03 mV. Bölüm 6.1'in kestirimi hiç değiştirilmeden çalıştırıldığında
filtrenin son

    (10.34 us / 1.953 us) = 5.3 nokta = 1.227 birim = 15.9 mV

üzerinde yumuşatma yapması gerekiyor; kedi için kestirilen 16.1 mV'a karşı. Bölüm
6.2'nin sayıları devreyi anlatıyorsa kelime de aynısını ölçmeli. Kediyi
anlatıyorsa ölçmemeli.

<img src="w2aew_outline_compare.png" alt="W2AEW gönderildiği ve geri okunduğu hali" width="460"> <img src="w2aew_scope.jpg" alt="w2aew_outline.py cihaz üzerinde" width="330">

**Şekil 5.** Kelimenin GP2 ve GP3'e gönderildiği hali, GP26 ve GP27 üzerinden
geri okunmuş hali ve cihazın her iki kanalda 500 mV/bölme ile gösterdiği hali.
Taban çizgisi boyunca uzanan köprü ve A'ya tırmanış üçünde de görünüyor.

**Tablo 5.** Aynı yöntemle ölçülen iki çizim. Her satır, taze bir yakalamanın bir
turu; `outline_compare.py` ve o çizime ait akış yazılımıyla alındı.

| Büyüklük | W2AEW | Kedi dış hattı | Kaynak |
| --- | --- | --- | --- |
| Tablodaki köşe sayısı | 486 | 368 | ayarlanmış |
| Çevre | 1666.8 birim | 1687.2 birim | türetilmiş |
| Noktalar arası aralık | 0.2315 birim = 3.00 mV | 0.2343 birim = 3.03 mV | türetilmiş |
| tau'dan kestirilen yumuşatma | 15.9 mV | 16.1 mV | türetilmiş |
| Yoldan sapma, ortalama | 14.3 mV | 14.3 mV | ölçülmüş |
| Yoldan sapma, ortanca | 11.2 mV | 12.6 mV | ölçülmüş |
| Yoldan sapma, en kötü | 57.6 mV | 55.9 mV | ölçülmüş |
| Tur başına ADC çifti | 632 | 629 | ölçülmüş |
| X aralığı, hedeflenen ve ölçülen | 3.092 V, 3.008 V | 3.041 V, 2.996 V | ölçülmüş |
| Y aralığı, hedeflenen ve ölçülen | 0.634 V, 0.647 V | 3.092 V, 3.028 V | ölçülmüş |

Kedi sütunu taze bir yakalama, bölüm 6.2'nin bildirdiği değil; turunun orada
kaydedilen 630 çifte karşı 629 çıkmasının sebebi bu: tur, rastgele bir noktada
başlayan bir paketin içinde bulunuyor, dolayısıyla uzunluğu çalışmalar arasında
bir iki örnek oynuyor.

İki ortalama 14.3 mV'ta uyuşuyor. Çizimler şekil, köşe sayısı ve çizgilerinin
gittiği yön bakımından farklı, nokta aralığı ve nokta başına süre bakımından aynı
olduğuna göre, bölüm 6.2'de ölçülen uzaklık kediye değil sinyal yoluna ait.
Buradaki kedi satırı aynı zamanda bölüm 6.2'nin daha sonraki bir yakalamada
tekrarı: orada kaydedilen 15.0 mV'a karşı 14.3 mV, yani aynı yazılımın iki
çalışması arasında % 5'lik bir yayılım; bu ölçümün dürüst hassasiyeti de bu.

## 7. Sonuç

Proje, kartın kendi ürettiği noktalardan XY kipinde bir resim çizmeyi hedefledi
ve bunu yapıyor. Pico 2'de olmayan bir DAC'ın yerini iki PWM pini ve iki RC
filtresi alıyor, ses çevre biriminden ödünç alınan bir DMA motoru nokta tamponunu
işlemci olmadan tekrar oynatıyor ve çizim ekranda sabit duruyor.

Akılda tutmaya değer şey, aynı filtrenin iki farklı hızda ne yaptığı. R ve C hiç
değiştirilmedi, yani tau baştan sona 10.34 us kaldı; ama bir noktaya verilen süre
on altı kat değiştirildi ve bu, tek bir devreyi iki farklı cihaza dönüştürüyor:

**Tablo 6.** Aynı filtrenin iki farklı kullanımı.

| | Bölüm 5, 32 kHz | Bölüm 6, 512 kHz |
| --- | --- | --- |
| Nokta başına süre | 31.25 us | 1.953 us |
| Zaman sabiti cinsinden | 3.02 tau | 0.189 tau |
| Bir nokta içinde yerleşme | % 95.1 | % 17.2 |
| Çizim başına nokta | 231 | 7200 |
| Çerçeve hızı | 138.5 Hz | 71.1 Hz |
| Nasıl çalışıyor | her noktaya ulaşılıyor | komşular ortalanıyor |

Soldaki sütun ders kitabı düzeni: filtreye üç zaman sabiti ver, bir sonraki
yazılmadan her koordinata ulaşsın. Sağdaki sütun bu kuralı çiğniyor ve yine de
çalışıyor, çünkü 1687 birimlik bir çevre üzerindeki 7200 nokta birbirinden
3.03 mV uzakta duruyor ve 3 mV'luk bir adımı verilen sürede takip edemeyen bir
filtre başarısız olmuyor, ortalama alıyor. Bölüm 6, bu ortalamanın bedelini
15.0 mV olarak ölçtü; yalnızca tau'dan kestirilen 16.1 mV ile aynı mertebede ve
gözle görülür bedeli bir çift körelmiş kulak ucu.

İki koşulun, herhangi bir bileşen değerinden daha önemli olduğu ortaya çıktı.
Çizim tek, kapalı ve sıralı bir yol olmalı, çünkü çerçeve belleği yok ve demeti
karartmanın bir yolu yok. Ve cihaz, kendisine gönderilen noktaları ayırt edecek
kadar hızlı örneklemeli; bu da devrenin değil osiloskobun bir özelliği. Şekil 3,
bu koşul düştüğünde aynı kartın bir nokta bulutu ürettiğini gösteriyor.
