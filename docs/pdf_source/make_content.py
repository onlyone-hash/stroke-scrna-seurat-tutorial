from pathlib import Path
import json
HERE=Path(__file__).parent
pages=[]
def p(t):return dict(type='p',text=t)
def h(t):return dict(type='sub',text=t)
def code(t,size=8.3):return dict(type='code',text=t,size=size)
def tab(rows,widths=None):return dict(type='table',rows=rows,**({'widths':widths} if widths else {}))
def box(label,text):return dict(type='callout',label=label,text=text)
def fig(name,height=280,caption=''):
    path=name if '/' in name else 'results/figures/'+name+'.png'
    return dict(type='figure',path=path,height=height,caption=caption)
def link(label,url):return dict(type='link',label=label,url=url)
def page(title,*blocks,section='动手复现'):
    pages.append(dict(title=title,section=section,blocks=list(blocks)))
REPO='https://github.com/onlyone-hash/stroke-scrna-seurat-tutorial'

page('从第一次点击，到看懂单细胞结果',
 p('**GSE174574 小鼠脑缺血单细胞 RNA 测序\nRStudio 零基础复现手册**'),
 p('适合：已安装 R 和 RStudio，但不熟悉界面、不知道代码放哪里、也不清楚单细胞图怎么读的学习者。无需 Git、Linux 或 Python 基础。本手册不介绍 R 的安装。'),
 fig('07_umap_celltypes',290,'本项目实际结果。每个点是一枚选中的细胞；图中的位置不是脑内空间位置。'),
 tab([['教学任务','本次基准'],['研究设计','3 份 Sham + 3 份 MCAO 后 24 h 小鼠脑样本'],['分析规模','6,000 个抽样细胞；17 个聚类'],['交付结果','15 张 PNG + 15 份 PDF；完整 CSV；本地重建 RDS']], [1,3]),
 box('使用方式','打开 PDF 的目录/书签，按页操作。每一步都看“成功标志”；不符合时先排查，不要连续重复点击运行。'),
 section='封面 · 教学抽样版')

page('01 先知道自己要完成哪几件事',
 p('建议分三次学习：第一次熟悉 RStudio 并跑通；第二次打开表格、重画和导出图；第三次理解质控、细胞注释及疾病差异。第一次不用急着改参数。'),
 tab([['阶段','对应内容','完成标志'],['准备','认识界面、下载、解压、打开项目','file.exists("run.R") 返回 TRUE'],['运行','恢复依赖、下载数据、一键分析','日志出现本次运行的 Completed'],['核查','验证文件、样本、计数与图','验证脚本打印 PASS'],['查看','读入 RDS/CSV，显示 UMAP 与基因图','Plots 出图，表格在查看器打开'],['导出','用 ggsave 保存练习图片','results/practice 中出现文件'],['解释','理解一枚细胞、一份样本、一个基因','能说清图的横纵轴与统计单位']], [1,2.1,2.2]),
 h('全书导航'),
 p('前半部分是鼠标和键盘操作；中段是分析流程与图解；后半部分是结果表、伪 bulk、报错排查和完整练习脚本。每页都有 PDF 书签，可在阅读器的“目录/书签”栏直接跳转。'),
 box('先保留一份原始项目','GitHub ZIP 已带交付时的图片和结果表。建议保留一份未改动的解压副本，另复制一份作为自己的练习项目。重新运行会覆盖同名结果。'),
 section='开始前')

page('02 这次分析的是哪些数据',
 p('GSE174574 是公开数据再分析。原作者完成了动物取材、单细胞建库与测序，并上传计数矩阵。我们从这个矩阵开始，不开展新的测序实验，也不从 FASTQ 重新比对。'),
 tab([['样本名','GEO 编号','条件'],['Sham1','GSM5319987','假手术'],['Sham2','GSM5319988','假手术'],['Sham3','GSM5319989','假手术'],['MCAO1','GSM5319990','脑缺血后 24 小时'],['MCAO2','GSM5319991','脑缺血后 24 小时'],['MCAO3','GSM5319992','脑缺血后 24 小时']], [1,1.6,2]),
 p('物种为小鼠，组织为左侧脑半球。Sham 为假手术对照；MCAO 指大脑中动脉阻塞模型。两组各 3 份样本，组间疾病比较以样本作为重复。'),
 box('58,528 和 6,000 为什么不同','下载矩阵共有 58,528 个细胞条形码。当前阈值下 58,326 个合格，再从每份样本中固定随机抽取 1,000 个，合计 6,000 个用于入门分析。'),
 link('官方数据：NCBI GEO / GSE174574','https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE174574'),
 section='认识研究对象')

page('03 单细胞矩阵里的数字是什么',
 p('一个基因是一行，一枚细胞是一列，格子里是该细胞中捕获并识别到的 UMI 计数。UMI 用于减少 PCR 扩增重复计数；它不是完整的细胞内 RNA 普查。'),
 tab([['玩具示例','细胞 A','细胞 B','细胞 C'],['P2ry12','6','0','1'],['Aqp4','0','8','0'],['Spp1','1','0','10']], [1.5,1,1,1]),
 p('上表仅解释格式，不是这次结果。barcode 是细胞条形码，用于区分细胞。不同样本可能有相同 barcode，因此项目会加上 Sham1_ 等前缀，避免混淆。'),
 h('这三个概念不要混'),
 tab([['词','在本教程中代表什么'],['细胞','一枚被捕获并测序的细胞，UMAP 中通常是一个点'],['样本','来自一只动物的一份脑组织测序样本，疾病统计的重复单位'],['基因','例如 Spp1、Aqp4；差异表中通常一行一个基因']], [1,4]),
 box('0 不等于“绝对没有表达”','可能表达本来很低而没被捕获到。RNA 表达也不直接等于蛋白数量、细胞功能或因果关系。'),
 section='认识数据')

page('04 文件、代码、对象、图片分别是什么',
 tab([['文件类型','你该怎样使用'],['.Rproj','RStudio 项目入口；打开它来定位工作目录'],['.R','代码脚本；在 Source 编辑区阅读和运行'],['.csv / .tsv','结果表或元数据；可以读进 R 查看'],['.mtx.gz + genes + barcodes','配套的稀疏计数矩阵文件，不要用 Import Dataset 手动拼接'],['.rds','保存的 R 对象；用 readRDS() 加载'],['.png / .pdf','已经保存到磁盘的图片/图稿'],['renv.lock','记录依赖版本，用于恢复软件环境']], [1.7,3.5]),
 h('三种“保存”不是一回事'),
 p('Ctrl+S 保存的是当前代码文件。把一个对象放进 Environment 只是暂存在内存。把图显示在 Plots 也不等于把图保存到磁盘。代码、对象、图片各有自己的保存方法。'),
 box('最常见的误会','重新打开 RStudio 后 obj 不见了，不代表分析结果丢失。只要本地 02_annotated.rds 仍在，用 readRDS() 就能重新加载。'),
 section='认识文件')

page('05 第一次打开 RStudio：只有三块也正常',
 fig('docs/pdf_source/assets/01_initial.jpg',340,'本机 RStudio 实际初始界面。尚未打开代码文件时，左侧可能只有 Console；右上是 Environment，右下是 Files / Plots 等标签。'),
 p('先按文字标签找区域，不要依赖“必须在左上角”的记忆。不同版本、窗口大小和个人布局可能不同。图中的 D:/R/Rworkdir 只是截图时的目录，不是你必须创建的路径。'),
 h('找不到脚本编辑区时'),
 p('点击最上方 File → New File → R Script。打开一个 .R 脚本后，Source 编辑区通常会出现。若某区域被最大化，可在 View → Panes 中找 Show All Panes，或使用区域边缘的还原按钮。'),
 box('先分清入口','RStudio 是编写和运行 R 的界面。我们在 Console / Source 中运行 R 代码；不要把本手册代码粘进 Terminal、网页搜索框或 Windows 命令提示符。'),
 section='认识 RStudio 界面')

page('06 四个区域：记住这张地图',
 dict(type='panemap'),
 p('这张是按常见布局绘制的操作示意图，不是一次正在运行分析的截图。区域位置可以调整；名称和作用更重要。'),
 tab([['编号','区域','最常用的动作'],['1','Source','输入、修改、保存脚本；选中代码后按 Ctrl+Enter'],['2','Console','看返回值、进度和报错；短命令输入后按 Enter'],['3','Environment','看 obj、qc_table 等对象是否已经存在'],['4','Files / Plots','Files 找磁盘文件；Plots 看当前会话绘图']], [0.6,1.4,3]),
 p('上方 Run 负责执行光标所在行或选中代码；Source 可执行整个当前脚本。右上 Project 菜单显示当前项目。第一次练习先用 Ctrl+Enter 一段段运行。'),
 section='认识 RStudio 界面')

page('07 下载项目：不需要安装 Git',
 p('步骤 1：在浏览器地址栏打开下方仓库链接。确认账号为 onlyone-hash，仓库名为 stroke-scrna-seurat-tutorial。'),
 link('打开项目 GitHub 首页',REPO),
 p('步骤 2：点击页面文件列表上方的绿色 Code 按钮，再点 Download ZIP。文件通常下载到 Windows“下载”文件夹。'),
 p('步骤 3：在文件资源管理器中找到 ZIP，右键 → 全部解压缩 / Extract All。选择你有写入权限、容量足够的位置。'),
 p('步骤 4：进入解压后的文件夹。外层文件夹可能叫 stroke-scrna-seurat-tutorial-main；继续进入，直到能同时看到 run.R、config、scripts、results 和 .Rproj 文件。'),
 code('run.R\nconfig/\nscripts/\nresults/\ndocs/\nstroke-scrna-seurat-tutorial.Rproj'),
 box('成功标志','同一层能看到 run.R 和 .Rproj；不再位于 ZIP 压缩包内部。不要只下载 run.R：它依赖其他脚本、配置和结果目录。'),
 p('建议将这一份复制一份作为练习副本。首次需联网下载约 263 MB 的表达矩阵文件，此外还需要下载 R 包。建议 16 GB 内存并预留数 GB 磁盘空间。'),
 section='下载与解压')

page('08 用 Open Project 打开正确文件',
 p('推荐方法：在文件资源管理器中，双击 stroke-scrna-seurat-tutorial.Rproj。若没有自动用 RStudio 打开，使用下面的菜单方法。'),
 h('RStudio 菜单方法'),
 p('① 点击最上方 File。\n② 点击 Open Project…（不要选 New Project）。\n③ 在文件选择窗口进入刚才的项目文件夹。\n④ 单击扩展名为 .Rproj 的文件。\n⑤ 点击 Open / 打开，等待 R 会话准备好。'),
 p('右上角 Project 通常会从 (None) 变成项目名；Source 可能恢复上次打开的文件。每个人的目录可以不同，不需要改成作者电脑的 D 盘路径。'),
 code('getwd()\nfile.exists("run.R")'),
 box('成功标志','点击 Console，逐行输入上面两行并按 Enter。第一行返回你的项目目录，第二行返回 [1] TRUE。若是 FALSE，先解决目录问题，再运行分析。'),
 p('不要用 File → Open File 只打开一个 run.R 就以为项目目录也已切换。打开脚本和打开项目是两种操作。'),
 section='打开项目')

page('09 第一行命令：在 Console 算 1 + 1',
 p('① 找到 Console 标签。\n② 在 > 右侧空白处单击，让光标落在输入行。\n③ 输入下方内容。\n④ 按键盘 Enter。'),
 code('1 + 1'),
 h('你应该看到'),code('[1] 2'),
 p('这里的 [1] 是 R 输出的元素位置提示，2 才是计算结果。你只输入 1 + 1；不要把 >、[1] 2 或 PDF 页码一起复制进去。'),
 tab([['符号或文字','含义','现在怎么做'],['>','R 正等待下一条命令','可以继续输入'],['+ 出现在新输入行开头','上一条命令可能没写完','按 Esc 取消，检查引号和括号'],['Error / 错误','本条命令失败','读清最后的错误内容'],['Warning / 警告','提醒，有时仍运行成功','结合是否出现正确结果判断']], [1.3,2.2,1.7]),
 box('复制代码规则','只复制浅色代码框里的代码。使用英文半角引号 " " 和括号 ( )。不要手工加入中文引号“ ”。'),
 section='第一次执行代码')

page('10 创建脚本：把练习保存下来',
 p('① 点击 File → New File → R Script；Windows 常用快捷键是 Ctrl+Shift+N。\n② 在新出现的 Source 编辑区输入下面几行。\n③ 按 Ctrl+S；在保存窗口选择项目文件夹，文件名写 my_first_practice.R，点击 Save。'),
 code('practice_values <- c(2, 4, 6, 8)\nmean(practice_values)'),
 p('④ 把光标放到第一行，按 Ctrl+Enter。\n⑤ 再把光标放到第二行，按 Ctrl+Enter。也可以选中两行后一次按 Ctrl+Enter。'),
 h('你应该看到什么'),
 p('Console 返回 [1] 5；Environment 中出现 practice_values。第一行的 <- 是赋值，把右侧的数值向量放到这个名字下面；第二行计算平均数。'),
 box('Run 与保存','运行成功不等于已经保存脚本。Ctrl+S 保存代码；Ctrl+Enter 执行代码。如果标签标题旁出现 *，通常说明有尚未保存的修改。'),
 p('本项目已提供 docs/teaching/01_RStudio_first_steps.R，可用 File → Open File 打开，逐行完成同样练习。你不必重新手打所有代码。'),
 section='Source / Run / Save')

page('11 跑一行、跑一段、跑整份：如何选择',
 tab([['想做什么','鼠标与键盘','适合什么时候'],['只运行一行','光标放该行 → Ctrl+Enter / Run','最初的简单练习'],['运行一个完整代码块','从开头拖选到结束 → Ctrl+Enter','if、函数或分多行的绘图代码'],['运行整份脚本','点击编辑区上方 Source','确认整份脚本都应该执行时']], [1.2,2.2,1.8]),
 code('plot(practice_values, type = "b", pch = 19,\n     col = "steelblue", xlab = "Index", ylab = "Value")'),
 p('把上面两行一起选中，再按 Ctrl+Enter。右下角点击 Plots，应出现带折线的点图。它是示例数字图，不是单细胞结果。'),
 box('不要同时按两次运行','长任务已经开始时，不要又点 Run 又点 Source，也不要重复按回车。可能会排入重复任务、覆盖输出或让你误以为卡住。'),
 p('源代码中的 # 后面是注释，通常不执行。看到 if (...) { ... } 时，要把整个块连同最后的 } 一起运行。不要只拷贝中间一行。'),
 p('本教程后面的长代码建议直接打开配套 .R 文件，在 Source 里选中指定块。PDF 复制如有断行问题，优先以 .R 文件为准。'),
 section='执行方式')

page('12 开始前检查：目录、版本和副本',
 p('现在已打开项目，先在 Console 逐行运行。它们只检查环境，不会启动分析。'),
 code('getwd()\nfile.exists("run.R")\nfile.exists("config/analysis_config.R")\nR.version.string'),
 tab([['检查','基准或预期'],['当前目录','包含本项目的 run.R、config 和 scripts'],['两个 file.exists','都为 TRUE'],['R 版本','本次基准为 R 4.4.1；其他兼容版本可能有细节差异'],['项目副本','保留原始结果，使用练习副本重跑'],['网络与容量','能访问 GitHub、NCBI、CRAN、Bioconductor；有足够空间']], [1.3,3.7]),
 box('若目录不对','优先重新通过 .Rproj 打开。备用：在 R 里 setwd("你的项目绝对路径")，Windows 建议用 /。setwd 只是切换目录，不会创建这个目录。'),
 code('setwd("D:/my_projects/stroke-scrna-seurat-tutorial-main")',7.9),
 p('上面是示例路径，必须换成你自己的位置。不要照抄后再疑惑为什么找不到文件。'),
 section='运行前核查')

page('13 第一次准备依赖：一段一段执行',
 p('打开 docs/teaching/02_reproduce_analysis.R。可以在右下 Files 中依次点 docs → teaching → 文件名；也可以 File → Open File，选择这个文件。'),
 h('先运行 Step A，再运行 Step B'),
 code('getwd()\nstopifnot(file.exists("run.R"))\n\noptions(repos = c(CRAN = "https://cloud.r-project.org"),\n        timeout = 900)\nif (!requireNamespace("renv", quietly = TRUE)) {\n  install.packages("renv")\n}\nrenv::restore(project = getwd(), prompt = FALSE)\nrenv::load(project = getwd())'),
 p('选中上面整个准备块后按 Ctrl+Enter，等待完成。install.packages 安装缺少的 renv；restore 依据 renv.lock 恢复依赖；load 让当前会话使用项目库。软件环境准备与下载测序数据是两件事。'),
 box('成功标志','依赖准备结束且没有 Error，Console 回到新的 >。首次安装可能比正式分析更慢。若弹出更新/重启提示，先读提示；不要把“所有包升级到最新”当成必须步骤。'),
 p('本手册没有声称已在每一台干净电脑上测试所有依赖下载。源码编译、旧版本包和系统差异仍可能影响恢复；报错排查页给出处理顺序。'),
 section='恢复 R 包环境')

page('14 包安装时：哪些信息需要看',
 tab([['看到的信息','通常意味着什么','建议动作'],['trying URL / downloaded / installing','正在下载或安装包','等候，不重复运行'],['DONE (包名)','某个包安装完成','继续等其他包'],['built under R version ...','包构建时的 R 版本不同','留意兼容性；不是单独判定失败的依据'],['there is no package called ...','当前会话找不到依赖','检查 restore 后是否 load；核对包名'],['non-zero exit status / compilation failed','安装或编译失败','查看最后一个失败的包及此前错误'],['permission denied / locked directory','权限、文件占用或中断安装问题','关闭占用会话后重试；不要删除整个 R 库']], [1.8,1.8,2.2]),
 h('最稳妥的排查顺序'),
 p('1. 截取最后一条 Error，并往前看第一个失败的包名。\n2. 核对当前目录和 R 版本。\n3. 核对网络是否能访问失败的官方地址。\n4. 如被要求使用 Rtools 编译，按与你的 R 匹配的官方工具说明处理。\n5. 再恢复依赖，勿随机升级、卸载一大批已工作的包。'),
 box('快速试跑是另一条路线','如果接受包版本可能不同，可直接 source("run.R", encoding="UTF-8")；脚本只补缺少的包。它适合先练流程，严格复现仍优先锁文件路线。'),
 section='依赖与网络')

page('15 启动分析：只执行这个入口一次',
 p('依赖准备好后，在 02_reproduce_analysis.R 中找到 Step C。选中下面这一行，按 Ctrl+Enter。'),
 code('source("run.R", encoding = "UTF-8")'),
 p('这条命令会按顺序运行下载、质控、抽样、标准化、聚类、细胞注释、差异分析、绘图和报告。你不需要打开 00_setup.R 到 05_report.R 挨个猜顺序。'),
 tab([['日志步骤','正在做什么'],['00_setup.R','检查依赖、随机种子和绘图设置'],['01_download.R','读取元数据、下载 18 个文件、计算 SHA256'],['02_preprocess.R','质控、抽样、标准化、PCA、聚类、UMAP'],['03_annotation.R','标记注释、人工复核、组成和基因图'],['04_pseudobulk.R','按样本汇总小胶质计数并进行 edgeR 检验'],['05_report.R','生成分析报告、摘要和锁文件']], [1.5,3.7]),
 box('正在运行时','看 Console 输出即可。可滚动查看此前日志，但不要连续提交相同命令。耗时取决于网络和电脑；本机的缓存运行时间不能保证适用于你的首次运行。'),
 section='一键执行')

page('16 下载的数据放在哪里，能不能中断',
 p('输入目录是 data/raw。每份样本有 matrix.mtx.gz、genes.tsv.gz、barcodes.tsv.gz 三个配套文件，六份样本共 18 个。R 可直接读压缩文件，不必手工解压 .gz。'),
 p('下载步骤使用官方 GEO HTTPS 链接。先写入 .part 临时文件，成功后再改为正式文件名；后续运行会复用完整文件，并与基准 SHA256 指纹比较。'),
 code('list.files("data/raw")\nfile.exists("config/input_checksums.tsv")'),
 p('以上命令应在前一个任务结束后再运行，不要在长分析运行中继续插入命令。下载超时可先解决网络再重试。校验不一致时重新获取异常文件；不要删除基准校验表来掩盖不一致。'),
 h('必须中止时'),
 p('在 RStudio 点击运行中 Console 的停止按钮，或尝试 Esc。中止后等 Console 回到 >，再检查最后完成的步骤。如果中止发生在安装包时，先解决安装状态；如果发生在数据下载，脚本的临时文件机制能减少误用半成品。'),
 box('手动下载备用','可从 GEO 的 Supplementary files 下载打包矩阵，再把其中 18 个 .gz 放进 data/raw，保持文件名不变。GEO 文件名 RAW.tar 是矩阵打包，不代表本教程从 FASTQ 开始。'),
 section='下载与中断')

page('17 怎样确认“这次真的跑完了”',
 p('基准 ZIP 已含此前生成的图，因此“看见图文件”本身不能证明你刚刚的运行成功。先检查本次 Console 的末尾和日志时间。'),
 code('file.show("results/logs/analysis.log")'),
 p('日志开头 Started 与结尾 Completed 应对应这次运行时间。没有 Completed 时，去 Console 查最后一条 Error；不要仅凭中间出现了一张图就判断完成。'),
 code('file.exists("results/objects/02_annotated.rds")\nlength(list.files("results/figures", pattern = "[.]png$"))\nlength(list.files("results/figures", pattern = "[.]pdf$"))'),
 h('基准运行的预期'),
 tab([['检查','期望'],['注释对象 RDS','TRUE；这个大对象不在 GitHub ZIP 中'],['PNG 数量','15'],['PDF 图稿数量','15'],['分析规模','6,000 个细胞、17 个聚类'],['小胶质检验','6 份样本；6,836 个被检验基因']], [1.5,3.7]),
 box('版本差异','主结果数字是本项目默认参数和记录环境的基准。改变软件版本、抽样数、质控或分辨率后，聚类和差异数可能变化，应记录变化原因。'),
 section='检查成功')

page('18 验证：文件齐全还不够',
 p('全部分析结束后，在 Console 或 Step D 执行：'),
 code('source("scripts/verify_results.R", encoding = "UTF-8")'),
 h('基准通过时会打印'),
 code('PASS: 6000 cells; 17 clusters; 6 samples;\n6836 tested genes; 15 PNG + 15 PDF;\nexact pseudobulk sums; input SHA256 verified.',8),
 p('上框为便于阅读换行展示；实际输出通常是一整行。它检查每细胞筛选记录与选中 barcode、样本组成、差异方向、FDR 范围、原始 UMI 汇总，以及输入文件指纹等。'),
 tab([['核查对象','为什么要核查'],['6 份样本','防止只剩一份对照或模型仍声称 3 vs 3'],['整数原始计数的精确和','防止把 log 表达或平均值交给 edgeR'],['barcode 对应','防止不同样本/对象误配'],['完整图和表','防止半途报错后仍交付残缺结果']], [1.7,3.5]),
 box('PASS 的边界','它说明文件和计算结构一致，不等于所有细胞注释已经被独立实验证实，更不等于已证明某基因的因果作用。'),
 section='结果一致性')

page('19 看懂整个分析顺序',
 dict(type='workflow'),
 p('标准化将每个细胞总计数差异做一定程度的调整，便于表达图和细胞结构分析。高变基因提供区分细胞的主要特征；PCA 先压缩维度，再建近邻图与聚类。UMAP 用二维图展示结构。'),
 p('细胞身份由多个标志基因辅助判断。最后挑选同一谱系的小胶质细胞，在每个样本内加总原始计数，形成六列伪 bulk 数据，进行疾病比较。'),
 tab([['阶段','使用的值'],['UMAP / 细胞结构','标准化及缩放后的表达表示，先经 PCA'],['FeaturePlot / DotPlot','log 标准化表达及检出比例'],['edgeR 疾病比较','每样本、同一细胞类型的原始 UMI 之和']], [1.7,3.5]),
 box('本教程保持简单','未运行专门双细胞检测、环境 RNA 校正、批次整合、细胞通信或拟时序。了解这些省略，才能正确限定结果用途。'),
 section='理解方法')

page('20 质控图：先看细胞质量',
 fig('01_qc_before',245,'过滤前全部下载条形码的指标分布；每格纵轴不同。'),
 tab([['指标','是什么','本项目筛选'],['nFeature_RNA','计数大于 0 的基因数','200 到 6,000'],['nCount_RNA','该细胞全部基因的 UMI 总数','不超过 25,000'],['percent.mt','线粒体基因 UMI 百分比','不超过 20%']], [1.6,2.5,1.5]),
 p('小提琴越宽，表示该范围细胞越多。看同一指标在六份样本中是否整体偏移。阈值不是所有单细胞实验的通用标准；脑缺血中的损伤细胞尤其可能受过滤影响。'),
 code('qc_table <- read.csv("results/tables/qc_summary.csv",\n                     fileEncoding = "UTF-8-BOM")\nView(qc_table)'),
 p('View 的 V 大写。表里的 qc_pass_cells 是合格数，analyzed_cells 是抽样后分析数。合格但没有抽中，与质控被删除是不同情况。'),
 section='读图 1 / 质控')

page('21 聚类与 UMAP：每点一枚细胞',
 fig('04_umap_clusters',325,'无监督聚类 UMAP。编号只是标签，没有天然的细胞身份。'),
 p('默认使用 PC1 到 PC20 建图，Louvain 聚类分辨率为 0.4。相似表达的细胞往往在局部相邻，但簇间距离和面积不能直接当成定量生物学差异。'),
 p('一类细胞可能分成多个簇；一个簇也可能混有几类细胞或技术影响。UMAP 的横纵轴不是脑内位置，也不是疾病时间轴，更不能仅凭图形推出分化关系。'),
 box('需要联合看','对比按 sample_id、group 和 cell_type 上色的图。若某簇主要来自一个样本，要考虑样本质量、技术差异与真实生物差异等可能。'),
 section='读图 2 / 聚类')

page('22 细胞名称是怎样得到的',
 fig('07_umap_celltypes',315,'同一个 UMAP，颜色换为基于多标记的暂定粗谱系标签。'),
 p('自动候选评分只提供辅助：逐基因标准化标记表达，计算组合分数，再比较每簇的第一、第二候选。它不是细胞身份概率，也不能称为注释准确率。'),
 p('人工复核保留了重要的不确定性：cluster 4 同时有周细胞和平滑肌标记，使用宽标签 Mural_cells；cluster 13 的 51 个细胞混有小胶质和内皮信号，标为 Uncertain，排除在小胶质差异分析之外。'),
 box('不强行套标签','粗注释适合入门。混合标记可能与双细胞、污染或生物学边界有关；本流程没有独立确认其原因。'),
 section='读图 3 / 细胞注释')

page('23 标记点图：用多个基因找证据',
 fig('09_marker_dotplot',275,'横轴基因、纵轴 cluster；点大小为检出百分比，颜色为逐基因缩放后的平均表达。'),
 p('先看成套标记是否集中，而不是只找最红的一个点。例如 P2ry12 与 Tmem119 支持小胶质身份；Cldn5 / Pecam1 支持内皮；Aqp4 / Slc1a3 支持星形胶质。'),
 p('颜色经过每个基因单独缩放，不能跨基因比较绝对分子数量。一个通用标记如 Lyz2 不能独自区分全部髓系细胞。'),
 h('检查对应证据表'),
 code('ann <- read.csv("results/tables/cluster_annotation.csv",\n                fileEncoding = "UTF-8-BOM")\nView(ann)'),
 box('本数据的具体提醒','Ttr 在多个非脉络丛谱系中普遍检出，提示需要注意背景 RNA。注释依赖组合证据；不能把所有 Ttr 阳性细胞都叫脉络丛细胞。'),
 section='读图 4 / 标记')

page('24 看到这些英文细胞名时',
 tab([['标签','中文理解','标记举例'],['Microglia','小胶质细胞；脑内驻留髓系免疫细胞','P2ry12 / Tmem119'],['Monocytes','单核细胞相关谱系','Ccr2 / Ly6c2'],['Macrophages','巨噬细胞相关谱系','Mrc1 / Lyve1'],['Neutrophils','中性粒细胞相关谱系','S100a8 / S100a9'],['Astrocytes','星形胶质细胞','Aqp4 / Slc1a3'],['Oligodendrocytes','少突胶质细胞','Mbp / Plp1'],['Endothelial','血管内皮细胞','Cldn5 / Pecam1'],['Mural_cells','血管壁细胞粗合并类','Rgs5 / Acta2'],['Fibroblasts','成纤维细胞相关谱系','Col1a1 / Dcn'],['Ependymal','室管膜细胞相关谱系','Foxj1 / Pifo'],['Choroid_plexus','脉络丛相关谱系','Ttr / Folr1'],['Uncertain','混合信号或证据不足','需进一步核查']], [1.8,2.6,1.7]),
 p('候选标记面板还包含其他类型，但不保证这次抽样都捕获到。取材、消化、细胞存活和捕获方式会影响谱系比例。这里的细胞名是暂定注释，不是单凭名称就完成了功能验证。'),
 section='英文标签速查')

page('25 组成图：比例不是绝对数量',
 fig('11_composition',300,'每根柱子为一份样本，颜色占比的分母是该样本进入分析的细胞数。'),
 p('先比较同一组的三个样本，再考虑两组差异。组成受到取材、消化、捕获、质控和抽样影响；某类比例降低，可能只是其他类比例升高造成的相对变化。'),
 p('不要把柱子直接写成“组织中小胶质细胞绝对数量显著下降”。本项目仅做描述性组成展示，不把许多细胞当作许多动物做组成检验。'),
 code('composition <- read.csv(\n  "results/tables/celltype_composition.csv",\n  fileEncoding = "UTF-8-BOM")\nView(composition)'),
 section='读图 5 / 组成')

page('26 重开 RStudio 后，先加载对象',
 p('完成分析后，可以关闭并再次打开项目。Environment 可能为空，这是正常的；大型 Seurat 对象已保存在本地 RDS 文件中。'),
 code('renv::load(project = getwd())\nlibrary(Seurat)\nlibrary(ggplot2)\n\nobj <- readRDS("results/objects/02_annotated.rds")\nobj\ntable(obj$sample_id, obj$cell_type)'),
 p('依次运行上面整块，等待对象载入。直接输入 obj 会打印对象概况；table 展示各样本、各暂定细胞类型的细胞数。Environment 中会出现 obj。'),
 box('找不到 RDS 时','GitHub ZIP 不含大型 RDS。必须先完整运行分析才能在你电脑上重建。若已有本地结果，检查工作目录，而不是从别的项目复制同名 RDS。'),
 p('readRDS() 是读对象；read.csv() 是读表。两者不能互换。RDS 包含表达矩阵、metadata、PCA 和 UMAP 等；它不是一张可以直接在表格软件中打开的表。'),
 section='重新载入')

page('27 自己在 Plots 画一张 UMAP',
 p('先完成前一页的对象载入。接着在 Source 新建练习脚本，或打开 03_view_and_plot_results.R 中的 UMAP 部分。'),
 code('p_umap <- DimPlot(\n  obj, reduction = "umap", group.by = "cell_type",\n  pt.size = 0.35\n)\nprint(p_umap)'),
 p('① 选中完整五行 → Ctrl+Enter。\n② 在右下区域点击 Plots 标签。\n③ 若图太小，点击 Plots 上方 Zoom；关闭放大窗口可回到 RStudio。'),
 fig('07_umap_celltypes',240,'你应看到与这张结构相同的细胞图；这里的基准成图另有配色和标题，因此样式可不同。'),
 box('为什么赋值后没自动出现图','p_umap <- ... 把图存到对象里；print(p_umap) 明确把图显示出来。在 source 脚本里尤其应该使用 print。'),
 section='动手画图 1')

page('28 看 Spp1 在哪些细胞表达',
 code('p_spp1 <- FeaturePlot(\n  obj, features = "Spp1", order = TRUE, pt.size = 0.35\n)\nprint(p_spp1)'),
 p('FeaturePlot 在既有 UMAP 坐标上，以颜色显示指定基因的 log 标准化表达。你可以把 Spp1 改成 P2ry12、Tmem119、Aqp4 或 Cldn5，观察分布是否符合注释。'),
 fig('10_gene_featureplots',255,'基准六基因图。每个子图是同一批细胞，不同基因的色阶不能直接跨基因比较绝对表达。'),
 code('"Spp1" %in% rownames(obj)'),
 box('找不到基因时','先核对英文大小写与拼写，运行上行检查是否存在。小鼠这里使用 Spp1；不要随意改成全大写的人类符号。某细胞计数为 0 也不等于绝对不表达。'),
 section='动手画图 2')

page('29 把图片保存到磁盘',
 p('先确认 p_umap 和 p_spp1 已经创建。然后运行以下代码，将练习图放进独立目录，保留原有基准图。'),
 code('dir.create("results/practice", recursive = TRUE,\n           showWarnings = FALSE)\n\nggsave("results/practice/my_celltype_umap.png",\n       plot = p_umap, width = 10, height = 7,\n       dpi = 300, bg = "white")\n\nggsave("results/practice/my_Spp1_map.pdf",\n       plot = p_spp1, width = 8, height = 6,\n       bg = "white")'),
 p('width 和 height 默认单位为英寸；dpi 影响 PNG 像素分辨率。PDF 适合矢量放大和进一步排版；修改后缀本身不能把一张位图变成矢量图。'),
 h('在 RStudio 中找到导出的文件'),
 p('① 点击右下 Files。\n② 如果当前不在项目根目录，点击目录面包屑或主页/项目入口返回项目。\n③ 依次进入 results → practice。\n④ 必要时点刷新图标，确认两个新文件名。\n⑤ 点击文件可按 RStudio/系统的选项预览或打开。'),
 box('成功标志','文件确实在 results/practice 中，不只是出现在 Plots 历史记录里。'),
 section='保存与导出')

page('30 如果想用 Plots 的 Export 按钮',
 p('这是一种交互导出方法，适合初学查看；正式复现优先保留 ggsave 代码，尺寸和路径更明确。'),
 p('① 在 Plots 中显示你要导出的图。\n② 点击该区域工具栏的 Export。\n③ 选择 Save as Image… 或 Save as PDF…。\n④ 在窗口中选择保存目录，填写文件名和宽高等参数。\n⑤ 点击 Save。\n⑥ 用 Files 或文件资源管理器重新找到文件并打开检查。'),
 tab([['情况','处理方式'],['Plots 没有图','先执行 print(p_umap)，再打开 Plots'],['文字/图例被截断','扩大图的宽高，再重新绘制和导出'],['只有 Viewer 中有内容','Viewer 与 Plots 不同；本项目的 ggplot 图显示在 Plots'],['Export 找不到或布局不同','使用前一页的 ggsave 代码完成同样任务'],['图片发白或透明','导出时使用白色背景；ggsave 中 bg = "white"']], [1.8,3.4]),
 box('自动流程与交互窗口不同','run.R 的图主要通过 ggsave 直接写磁盘。整个分析成功后，Plots 仍然可能为空；这不代表没有生成图。到 results/figures 检查自动输出。'),
 section='鼠标导出备选')

page('31 打开 CSV：用 View 看结果表',
 code('de_table <- read.csv(\n  "results/tables/microglia_pseudobulk_DE_all.csv",\n  fileEncoding = "UTF-8-BOM"\n)\nView(de_table)'),
 p('选中完整代码块运行。数据查看器通常在 Source 区域的新标签打开。它适合浏览、排序、过滤；并不等于你正在修改原始 CSV。'),
 p('可以点击列名查看排序，使用查看器的 Filter / 搜索功能缩小显示范围。想保留筛选结果时，应在 R 中生成新对象并另存文件。'),
 code('de_table[de_table$gene %in%\n           c("Spp1", "Lpl", "P2ry12", "Apoe"), ]\n\nde_selected <- subset(\n  de_table, FDR < 0.05 & abs(logFC) >= 1\n)\nnrow(de_selected)'),
 box('成功标志','按默认基准，全表有 6,836 行被检验基因；联合筛选子集有 1,216 行，即 548 较高 + 668 较低。不要把“未被检验”与“不显著”混为一谈。'),
 section='读表与筛选')

page('32 为什么疾病比较按样本汇总',
 p('同一只动物的许多细胞共享处理、取样和背景，不能当成许多只独立动物。我们在每份样本内，把已注释小胶质细胞的原始 UMI 按基因相加，得到基因 × 6 样本矩阵。'),
 tab([['样本','用于伪 bulk 的小胶质细胞数'],['Sham1','219'],['Sham2','203'],['Sham3','238'],['MCAO1','191'],['MCAO2','198'],['MCAO3','219']], [1.4,3.8]),
 p('统计重复仍是 3 vs 3 样本。不能把所有 Sham 细胞先合成一列、所有 MCAO 合成一列，否则会丢失组内重复。'),
 p('每份样本至少要有 20 个被注释的小胶质细胞，本项目才继续分析；不够时应复核或增加抽样，不会把缺失样本作为零表达。'),
 box('伪 bulk 不是“随便平均”','使用整数原始计数求和，再由 edgeR 处理文库大小、组成与样本变异。不要把 log 标准化表达直接加总后冒充原始计数。'),
 section='理解统计单位')

page('33 差异表各列怎样解释',
 tab([['字段','含义'],['gene','基因名称'],['logFC','模型估计的 log2(MCAO / Sham)；正数为 MCAO 较高'],['logCPM','平均表达水平的概括'],['F','quasi-likelihood F 检验统计量'],['PValue','未经多重比较校正的 P 值'],['FDR','多重检验调整后的统计量'],['direction','根据 FDR 和效应量阈值生成的显示类别']], [1.4,3.8]),
 p('本项目筛选：FDR < 0.05 且 abs(logFC) ≥ 1。logFC = 1 约对应 2 倍，-1 约对应一半，但实际解释仍应结合表达量和样本一致性。'),
 tab([['类别','怎样读'],['Higher_in_MCAO','达到联合阈值，MCAO 较高'],['Lower_in_MCAO','达到联合阈值，MCAO 较低'],['Below_threshold','未满足该联合阈值；不等于证明完全无差异']], [2,3.2]),
 box('FDR 不是什么','不是“这个基因有 95% 概率是真的”，更不是“这个基因导致脑梗死的概率”。表达关联需要独立证据才能支持机制。'),
 section='差异统计词典')

page('34 火山图：方向和统计证据一起看',
 fig('12_microglia_volcano',325,'一个点是一个被检验基因，不是一枚细胞。横轴 log2FC，纵轴 -log10(FDR)。'),
 p('越向右表示 MCAO 较高，越向左表示 Sham 相对较高；越高表示 FDR 越小。竖虚线是 ±1，横虚线对应 FDR 0.05。灰色表示未达到联合筛选门槛。'),
 p('本次基准中 Spp1、Lpl、Il1b 较高，P2ry12、Tmem119 较低；Apoe 未达门槛。不要因为某基因热门，或者单细胞图颜色较深，就把它写成显著变化。'),
 box('图上的标签只是部分基因','没标名字不代表没有结果。完整数据应去 microglia_pseudobulk_DE_all.csv 查询。'),
 section='读图 6 / 火山图')

page('35 热图与样本点图：看三个重复',
 fig('14_microglia_sample_expression',290,'每个点是一份样本，组内只有 3 个点。不是把所有细胞画成独立重复。'),
 p('纵轴是 TMM log2 CPM，每个基因子图可有不同范围。先看三个样本的方向与波动，再结合完整差异表里的 logFC 和 FDR；不要只看一条均值线。'),
 p('13_microglia_heatmap 热图中，每行是一个基因，每列是一份样本。每个基因在六个样本中分别做 Z 标准化，所以颜色只表示该基因在样本间的相对高低。'),
 box('不要跨行比绝对表达','红色基因 A 不一定比蓝色基因 B 分子数更多。热图基因来自同一数据的差异排序，分组清楚不等于又完成了一次独立验证。'),
 section='读图 7 / 样本表达')

page('36 找错第一步：不要重跑一切',
 tab([['问题','最先检查','修复方向'],['找不到 run.R','getwd() 与 file.exists','重新打开正确 .Rproj'],['Console 一直出现 +','引号、括号、花括号是否配对','Esc 取消，重新运行完整代码块'],['unexpected symbol','中文引号、复制了提示符或正文','改为英文半角标点，优先打开 .R 文件'],['object obj not found','当前会话是否载入 RDS','先 library 与 readRDS'],['找不到基因','符号大小写、rownames(obj)','核对小鼠基因名与是否被检出'],['找不到 RDS','分析是否完整运行、目录是否正确','ZIP 不带大对象；在本机重建']], [1.6,1.9,2.4]),
 h('保存报错信息的方法'),
 p('选中 Console 中最后一条 Error 以及之前第一个失败步骤，复制到纯文本，附上你刚运行的命令、getwd() 和 R.version.string。这样别人能定位问题。不要只说“跑不出来”。'),
 box('不要随意清空对象或删数据','先确认错误发生在哪一步。清空 Environment 不能修复路径或依赖；删除原始下载目录可能只会增加重复下载。'),
 section='报错排查 1')

page('37 网络、内存和图形报错',
 tab([['现象','优先处理'],['download timeout','确认官方站点可访问，等待或稍后重试；检查 .part 与 SHA256 报错'],['包安装失败','读最早失败的包和安装日志；核对 R 版本、网络与编译工具'],['cannot allocate vector','保持每样本 1,000 的默认抽样，不把完整 counts 转 dense；关闭不需的会话'],['绘图窗口太小','放大 Plots / Zoom；增加 ggsave 宽高'],['Plots 空白但自动运行成功','检查 results/figures；自动流程主要写文件'],['PDF 复制代码后失败','直接打开随附的 .R 文件，不手动猜换行'],['unexpected end of input / invalid input','检查源码 UTF-8、中文标点、括号；必要时按下面方法重启']], [1.7,3.5]),
 h('重启 R 后怎么继续'),
 p('通过 Session → Restart R 可重启当前 R 会话，Windows 常用快捷键为 Ctrl+Shift+F10。它会丢失尚未保存的内存对象，但不会自动删除已经写好的 RDS 和图片。先保存脚本，再重启。'),
 p('重启后重新打开项目、renv::load()、加载所需包，并用 readRDS() 读取对象。只想看图时不必重新下载、聚类和检验。'),
 section='报错排查 2')

page('38 第二天回来：最短查看路线',
 p('如果你昨天已经成功运行并生成 RDS，今天只需要看图或导出，按照下面顺序。'),
 p('① 双击项目 .Rproj。\n② 打开 docs/teaching/03_view_and_plot_results.R。\n③ 确认 getwd() 对应当前项目。\n④ 执行加载环境、包和 RDS 的部分。\n⑤ 执行需要的绘图代码，并用 print() 显示。\n⑥ 执行 ggsave 保存到 results/practice。'),
 code('renv::load(project = getwd())\nlibrary(Seurat)\nlibrary(ggplot2)\nobj <- readRDS("results/objects/02_annotated.rds")\n\np_umap <- DimPlot(obj, group.by = "cell_type")\nprint(p_umap)'),
 box('什么情况下才重新跑全部','更换输入数据、修改抽样/质控/聚类参数、需要从原始计数重新核算时。仅仅关闭了 RStudio，或 Plots 历史为空，不构成重做全部分析的理由。'),
 p('练习完成后用 Ctrl+S 保存你写的 .R 脚本。退出时不要依赖保存整个 .RData；保持脚本和明确的 RDS 入口，下一次更容易复现。'),
 section='重开与继续')

page('39 想改参数，先复制项目',
 p('参数集中在 config/analysis_config.R。第一次学习建议保持默认值。要做敏感性练习，先另复制一份完整项目，避免覆盖这次基准结果。'),
 tab([['参数','默认','改动影响'],['max_cells_per_sample','1000','增加后内存/耗时和稀有细胞捕获可能增加'],['max_percent_mt','20','改变被保留的损伤/应激等细胞状态'],['dims','1:20','影响近邻图、聚类和 UMAP'],['resolution','0.4','通常影响聚类精细程度'],['seed','20261026','影响抽样和随机计算']], [2,1,2.2]),
 box('全量不是第一次练习的必需项','把 max_cells_per_sample 改为 Inf 会使用全部质控合格细胞，资源需求明显增加。本手册的 6,000 细胞基准数字不再适用。'),
 p('参数变化后 cluster 编号可能改变。config/annotation_overrides.tsv 中对 cluster 4、13 的人工映射不能照搬，必须依据新点图和标记重新复核。'),
 p('一次只改一个因素，另存参数、软件版本和日志；比较主要谱系标记、样本保留比例和基因效应方向，不只追求更多显著基因或更好看的 UMAP。'),
 section='进阶边界')

page('40 本结果能讲什么，不能讲什么',
 h('可以支持的描述'),
 p('在这套小鼠急性脑缺血数据及当前分析条件下，不同粗谱系呈现不同表达特征；小胶质细胞的若干身份和反应相关基因在 MCAO 与 Sham 样本间存在转录关联。'),
 h('需要补充证据的问题'),
 p('某基因是否造成损伤或保护？某细胞究竟从哪里来、是否转化成另一类型？RNA 变化是否对应蛋白定位或功能？候选药物是否有效？这些需要本项目没有提供的独立设计和实验验证。'),
 tab([['限制','对解释的影响'],['每组 3 份样本','样本层面不确定性仍大'],['教学抽样','稀有亚群可能缺失，差异功效和边界可能改变'],['暂定标记注释','活化髓系细胞共享标记，存在边界不确定性'],['未做污染与双细胞专门校正','混合信号需谨慎解释'],['无批次整合','图中可能同时含技术和疾病差异'],['小鼠 24 小时急性期','不能直接代表人类患者或长期恢复']], [1.8,3.4]),
 box('写作时保留限定','使用“该数据中”“本次抽样再分析提示”“表达关联”；不要仅凭这次结果给细胞硬套 M1/M2 或宣布已证实治疗机制。'),
 section='科学解释')

page('41 一页核对：交作业前看这里',
 tab([['核查项','你应能做到'],['项目定位','解释 .Rproj 与 run.R 的区别，工作目录正确'],['代码操作','会在 Source 保存脚本、选中完整块运行'],['分析成功','本次日志有 Completed，不只依赖 ZIP 旧图'],['结果验证','verify_results.R 通过'],['图表齐全','15 PNG + 15 PDF，能找到真实磁盘文件'],['对象载入','知道 GitHub 不含 RDS，能在本机 readRDS'],['重新作图','能在 Plots 显示自己的 UMAP 和 Spp1 图'],['保存输出','results/practice 中有新 PNG / PDF'],['统计单位','UMAP 一点一细胞；疾病重复是一份样本'],['结论边界','能说明抽样、暂定注释、未校正因素和物种限制']], [1.6,3.6]),
 h('Windows 常用快捷键'),
 p('Ctrl+S 保存脚本；Ctrl+Enter 运行当前行/选中块；Ctrl+1 到 Source；Ctrl+2 到 Console；Ctrl+L 清空 Console 显示；Esc 取消未完成命令或尝试中断。Mac 的键位可能不同，以菜单提示为准。'),
 box('Ctrl+L 不会删除数据','它清理显示，不清空对象，也不删除文件。Environment 空了与磁盘文件丢了也是不同概念。'),
 section='验收清单')

page('42 完整练习脚本 1：RStudio 入门',
 p('文件：docs/teaching/01_RStudio_first_steps.R。下面每行都可在 Source 中逐步运行；开头的 # 行是说明。'),
 dict(type='sourcecode',path='docs/teaching/01_RStudio_first_steps.R',size=8.3),
 tab([['代码','成功标志'],['1 + 1','[1] 2'],['mean(practice_values)','[1] 5'],['plot(...)','Plots 出现示例折线点图'],['file.exists("run.R")','[1] TRUE'],['R.version.string','显示你实际使用的 R 版本']], [2.2,3]),
 section='附录 · 可复制代码')

page('43 完整练习脚本 2：一键复现',
 p('文件：docs/teaching/02_reproduce_analysis.R。先打开 .Rproj；依次执行 A、B、C、D。C 步骤只启动一次，等结束后再做 D。'),
 dict(type='sourcecode',path='docs/teaching/02_reproduce_analysis.R',size=8.1),
 box('这份脚本会真正运行分析','会下载输入、生成对象并覆盖同名结果。仅想查看已完成结果时，使用下一份脚本。'),
 section='附录 · 可复制代码')

page('44 完整练习脚本 3：载入与画图',
 p('文件：docs/teaching/03_view_and_plot_results.R 的前半部分。必须先在本机生成注释对象。'),
 dict(type='sourcecode',path='docs/teaching/03_view_and_plot_results.R',split='# Save practice figures',part=0,size=8.2),
 box('View 与 print','View 打开表格查看器；print 显示图对象。两者的大小写、拼写和用途不要互换。'),
 section='附录 · 可复制代码')

page('45 完整练习脚本 3：保存与查表',
 p('接上一页。也可以直接打开同一份 .R 文件，顺着往下运行。'),
 dict(type='sourcecode',path='docs/teaching/03_view_and_plot_results.R',split='# Save practice figures',part=1,size=8.1),
 box('复制提示','以 # 开头的是说明注释。只复制代码框内容，不复制文件路径、页码或说明正文。直接使用配套 .R 脚本最稳妥。'),
 section='附录 · 可复制代码')

page('46 资料来源与下一步',
 p('本手册以已实际运行的项目为例，新增面向 RStudio 新人的操作说明、示意图和练习。RStudio 初始界面为本机截图；四区域地图为明确标注的操作示意。所有单细胞结果图由 R 生成。'),
 link('项目首页、代码与完整结果',REPO),
 link('原始数据：NCBI GEO GSE174574','https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE174574'),
 link('原始研究：Zheng 等，DOI 10.1177/0271678X211026770','https://doi.org/10.1177/0271678X211026770'),
 link('Posit 官方：RStudio 界面布局','https://docs.posit.co/ide/user/ide/guide/ui/ui-panes.html'),
 link('Posit 官方：打开和管理 RStudio 项目','https://docs.posit.co/ide/user/ide/guide/code/projects.html'),
 link('Posit 官方：执行 R 脚本代码','https://docs.posit.co/ide/user/ide/guide/code/execution.html'),
 link('Seurat 官方：Guided Clustering Tutorial','https://satijalab.org/seurat/articles/pbmc3k_tutorial'),
 link('edgeR 官方用户指南','https://bioconductor.org/packages/release/bioc/vignettes/edgeR/inst/doc/edgeRUsersGuide.pdf'),
 link('renv 官方文档','https://rstudio.github.io/renv/'),
 p('更完整的方法解释和结果字段定义，还可阅读项目 docs/中文详细教程.md 与 docs/结果文件字典.md。界面菜单在不同版本可能略有变化，优先按文字标签和功能定位。'),
 box('复现范围与许可','此手册对应默认教学抽样基准，不是新实验或原论文所有图的重现。自行编写的代码与教学文本沿用项目 MIT 许可；原始数据使用仍应引用原作者。'),
 section='参考与说明')

(HERE/'handbook_content.json').write_text(json.dumps(pages,ensure_ascii=False,indent=2),encoding='utf-8')
print(f'Prepared {len(pages)} pages')
